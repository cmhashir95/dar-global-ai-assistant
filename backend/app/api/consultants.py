from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import scheduler_agent
from app.models.database import Booking, Lead, get_db
from app.models.schemas import BookingConfirmation, BookingRequest

router = APIRouter(prefix="/api/consultants", tags=["consultants"])


@router.get("")
def list_consultants():
    return scheduler_agent._load_consultants()


@router.get("/{consultant_id}/availability")
def get_availability(consultant_id: str, db: Session = Depends(get_db)):
    consultant = scheduler_agent.get_consultant(consultant_id)
    if not consultant:
        raise HTTPException(404, "Consultant not found")
    booked = scheduler_agent.booked_slots_by_consultant(db).get(consultant_id, set())
    calendar = scheduler_agent.generate_calendar(consultant_id)
    return [
        {"start": s["start"], "end": s["end"], "available": s["available"] and s["start"].isoformat() not in booked}
        for s in calendar
    ]


@router.post("/book", response_model=BookingConfirmation)
def book_slot(req: BookingRequest, db: Session = Depends(get_db)):
    consultant = scheduler_agent.get_consultant(req.consultant_id)
    if not consultant:
        raise HTTPException(404, "Consultant not found")

    # Re-validate the slot is still free server-side (agentic scheduling
    # must never trust a client-provided slot blindly -- this is the
    # concurrency/integrity guard for the booking action).
    booked = scheduler_agent.booked_slots_by_consultant(db).get(req.consultant_id, set())
    if req.slot_start.isoformat() in booked:
        raise HTTPException(409, "That slot was just booked by someone else. Please choose another.")

    lead = db.get(Lead, req.session_id)
    if lead is None:
        lead = Lead(session_id=req.session_id)
        db.add(lead)
    lead.buyer_name = req.buyer_name
    lead.buyer_email = req.buyer_email
    lead.buyer_phone = req.buyer_phone or lead.buyer_phone
    lead.assigned_consultant = req.consultant_id
    lead.status = "scheduled"

    booking = Booking(
        id=f"BOOK-{uuid.uuid4().hex[:10]}",
        session_id=req.session_id,
        consultant_id=req.consultant_id,
        consultant_name=consultant["name"],
        property_id=req.property_id,
        slot_start=req.slot_start,
        slot_end=req.slot_start + timedelta(minutes=scheduler_agent.SLOT_MINUTES),
        status="confirmed",
    )
    db.add(booking)
    db.commit()

    return BookingConfirmation(
        booking_id=booking.id,
        consultant_name=consultant["name"],
        consultant_email=consultant["email"],
        slot_start=booking.slot_start,
        slot_end=booking.slot_end,
        status="confirmed",
    )
