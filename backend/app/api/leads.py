from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import Lead, get_db
from app.models.schemas import LeadDetail, LeadSummary

router = APIRouter(prefix="/api/leads", tags=["leads"])


def _to_summary(lead: Lead) -> LeadSummary:
    return LeadSummary(
        session_id=lead.session_id,
        buyer_name=lead.buyer_name,
        buyer_email=lead.buyer_email,
        buyer_phone=lead.buyer_phone,
        last_intent=lead.last_intent,
        interested_properties=lead.interested_properties_list(),
        preferences=lead.preferences_dict(),
        assigned_consultant=lead.assigned_consultant,
        status=lead.status,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.get("", response_model=list[LeadSummary])
def list_leads(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.updated_at.desc()).all()
    return [_to_summary(l) for l in leads]


@router.get("/{session_id}", response_model=LeadDetail)
def get_lead(session_id: str, db: Session = Depends(get_db)):
    lead = db.get(Lead, session_id)
    if lead is None:
        raise HTTPException(404, "Lead not found")
    summary = _to_summary(lead)
    messages = [
        {"role": m.role, "content": m.content, "intent": m.intent, "grounded": m.grounded, "created_at": m.created_at}
        for m in sorted(lead.messages, key=lambda m: m.created_at)
    ]
    return LeadDetail(**summary.model_dump(), messages=messages)
