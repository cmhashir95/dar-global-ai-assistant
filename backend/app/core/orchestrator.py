from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.config import settings
from app.core import scheduler_agent
from app.core.guardrails import gate_response, HARD_GATED_INTENTS
from app.core.intent_classifier import classify_intent
from app.core.rag_engine import answer_property_question
from app.models.database import Lead, Message
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    Intent,
    ProposedSlot,
    RetrievedProperty,
)

GREETING_REPLY = (
    "Hello! I'm the Dar Global property assistant. I can share details on our developments in "
    "Dubai, Riyadh, London, and Marbella, or set up a call with one of our sales consultants. "
    "What are you looking for?"
)

FAQ_FALLBACK_REPLY = (
    "I can help with questions about specific Dar Global properties, pricing, or booking a call "
    "with a sales consultant. Could you tell me a bit more about what you're looking for -- "
    "a location, property type, or budget range?"
)


def _get_or_create_lead(db: Session, req: ChatRequest) -> Lead:
    lead = db.get(Lead, req.session_id)
    if lead is None:
        lead = Lead(session_id=req.session_id, status="new")
        db.add(lead)
    if req.buyer_name:
        lead.buyer_name = req.buyer_name
    if req.buyer_email:
        lead.buyer_email = req.buyer_email
    if req.buyer_phone:
        lead.buyer_phone = req.buyer_phone
    return lead


def _recent_context(db: Session, session_id: str, limit: int = 6) -> str:
    msgs = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    msgs.reverse()
    return "\n".join(f"{m.role}: {m.content}" for m in msgs)


def _record_message(db: Session, session_id: str, role: str, content: str, intent: str | None = None, grounded: bool | None = None):
    db.add(
        Message(
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            grounded=None if grounded is None else str(grounded).lower(),
        )
    )


def _handle_property_or_pricing(db: Session, lead: Lead, req: ChatRequest, context: str) -> ChatResponse:
    result = answer_property_question(req.message, context)

    retrieved = [
        RetrievedProperty(id=h["property"]["id"], name=h["property"]["name"], city=h["property"]["city"], score=h["score"])
        for h in result.retrieved
    ]
    if retrieved:
        ids = set(lead.interested_properties_list()) | {r.id for r in retrieved}
        lead.interested_properties = json.dumps(sorted(ids))
    lead.status = "qualifying" if lead.status == "new" else lead.status

    return ChatResponse(
        session_id=req.session_id,
        intent=Intent.PROPERTY_INQUIRY,
        reply=result.reply,
        grounded=result.grounded,
        retrieved_properties=retrieved,
    )


def _handle_schedule_call(db: Session, lead: Lead, req: ChatRequest, context: str) -> ChatResponse:
    full_text = f"{context}\nuser: {req.message}"
    extracted = scheduler_agent.extract_interest_tags(full_text)
    tags = extracted.get("tags", [])

    prefs = lead.preferences_dict()
    prefs.update({"tags": tags, "city": extracted.get("city", ""), "purpose": extracted.get("purpose", "unclear")})
    lead.preferences = json.dumps(prefs)

    booked = scheduler_agent.booked_slots_by_consultant(db)
    matches = scheduler_agent.find_best_consultants(tags, booked, top_n=3)

    proposed: list[ProposedSlot] = []
    for m in matches:
        for slot in m.next_available_slots[:2]:
            proposed.append(
                ProposedSlot(
                    consultant_id=m.consultant["id"],
                    consultant_name=m.consultant["name"],
                    slot_start=slot["start"],
                    slot_end=slot["end"],
                    match_score=m.expertise_score,
                    match_reasons=m.matched_tags or ["general availability"],
                )
            )

    if proposed:
        best = matches[0]
        reply = (
            f"Based on what you're looking for, {best.consultant['name']} ({best.consultant['title']}) "
            f"is our best-fit consultant"
            + (f" for {', '.join(best.matched_tags)}" if best.matched_tags else "")
            + f". Here are some upcoming times -- pick one and I'll confirm the booking:"
        )
        lead.status = "scheduled"
        lead.assigned_consultant = best.consultant["id"]
    else:
        reply = (
            "I couldn't find an open slot with our consultants in the next few days. "
            "I've noted your request and a Dar Global representative will follow up directly."
        )
        lead.status = "escalated"

    return ChatResponse(
        session_id=req.session_id,
        intent=Intent.SCHEDULE_CALL,
        reply=reply,
        grounded=True,
        proposed_slots=proposed,
    )


def handle_chat_turn(db: Session, req: ChatRequest) -> ChatResponse:
    lead = _get_or_create_lead(db, req)
    context = _recent_context(db, req.session_id)
    _record_message(db, req.session_id, "user", req.message)

    intent_result = classify_intent(req.message, context)
    lead.last_intent = intent_result.intent.value

    # --- Hard gate: never let off-topic / injection attempts reach the LLM
    # generator. Fixed canned response only.
    canned = gate_response(intent_result.intent)
    if intent_result.intent in HARD_GATED_INTENTS or intent_result.intent == Intent.COMPLAINT_OR_ESCALATION:
        if intent_result.intent == Intent.COMPLAINT_OR_ESCALATION:
            lead.status = "escalated"
        _record_message(db, req.session_id, "assistant", canned, intent=intent_result.intent.value, grounded=True)
        db.commit()
        return ChatResponse(
            session_id=req.session_id,
            intent=intent_result.intent,
            reply=canned,
            grounded=True,
            handoff_to_human=(intent_result.intent == Intent.COMPLAINT_OR_ESCALATION),
        )

    if intent_result.intent == Intent.GREETING:
        response = ChatResponse(session_id=req.session_id, intent=Intent.GREETING, reply=GREETING_REPLY, grounded=True)

    elif intent_result.intent in (Intent.PROPERTY_INQUIRY, Intent.PRICING_QUESTION):
        response = _handle_property_or_pricing(db, lead, req, context)

    elif intent_result.intent == Intent.SCHEDULE_CALL:
        response = _handle_schedule_call(db, lead, req, context)

    else:  # general_faq
        response = ChatResponse(session_id=req.session_id, intent=Intent.GENERAL_FAQ, reply=FAQ_FALLBACK_REPLY, grounded=True)

    # Session-level guardrail: too many turns without resolving -> offer a human.
    turn_count = db.query(Message).filter(Message.session_id == req.session_id, Message.role == "user").count()
    if turn_count >= settings.max_turns_before_human_handoff and lead.status not in ("scheduled", "escalated"):
        response.handoff_to_human = True
        response.disclaimer = "This conversation has been open a while -- I can loop in a human consultant any time."

    _record_message(db, req.session_id, "assistant", response.reply, intent=intent_result.intent.value, grounded=response.grounded)
    db.commit()
    return response
