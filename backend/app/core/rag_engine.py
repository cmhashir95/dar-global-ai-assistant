from __future__ import annotations

from dataclasses import dataclass

from app.core.guardrails import (
    SYSTEM_PROMPT,
    check_grounding,
    FALLBACK_UNGROUNDED_REPLY,
)
from app.utils.llm_client import chat_completion
from app.utils.vector_store import get_vector_store

RETRIEVAL_SCORE_THRESHOLD = 0.15  # below this, we treat the match as "not relevant enough"


@dataclass
class RagResult:
    reply: str
    grounded: bool
    retrieved: list[dict]  # [{"property": {...}, "score": float}]


def _build_context_block(retrieved: list[dict]) -> str:
    if not retrieved:
        return "No matching properties were found in the catalog for this query."
    lines = []
    for hit in retrieved:
        p = hit["property"]
        lines.append(
            f"- [{p['id']}] {p['name']} | {p['city']}, {p['country']} | {p['type']} | "
            f"Status: {p['status']} | Handover: {p['handover']} | Bedrooms: {p['bedrooms']} | "
            f"Price: ${p['price_from_usd']:,}-${p['price_to_usd']:,} | "
            f"Size: {p['size_sqft'][0]}-{p['size_sqft'][1]} sqft | "
            f"Amenities: {', '.join(p['amenities'])} | Payment plan: {p['payment_plan']} | "
            f"Notes: {p['highlights']}"
        )
    return "\n".join(lines)


def answer_property_question(user_message: str, conversation_context: str = "") -> RagResult:
    store = get_vector_store()
    hits = [h for h in store.search(user_message, top_k=3) if h["score"] >= RETRIEVAL_SCORE_THRESHOLD]
    context_block = _build_context_block(hits)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"CONTEXT (the only source of truth you may use):\n{context_block}\n\n"
                f"Conversation so far:\n{conversation_context}\n\n"
                f"Visitor's message:\n{user_message}\n\n"
                "Answer using only CONTEXT. Cite property IDs. If CONTEXT doesn't answer the "
                "question, say so and offer to connect them with a consultant."
            ),
        },
    ]
    reply = chat_completion(messages, temperature=0.2, max_tokens=350)

    retrieved_ids = [h["property"]["id"] for h in hits]
    grounding = check_grounding(reply, retrieved_ids)

    if not grounding.grounded:
        # Fail closed: if the model's own answer can't be verified against
        # what was retrieved, we discard it and return a safe fallback
        # instead of risking a hallucinated price/spec reaching the user.
        return RagResult(reply=FALLBACK_UNGROUNDED_REPLY, grounded=False, retrieved=hits)

    return RagResult(reply=reply, grounded=True, retrieved=hits)
