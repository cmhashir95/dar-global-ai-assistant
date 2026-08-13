from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Intent(str, Enum):
    GREETING = "greeting"
    PROPERTY_INQUIRY = "property_inquiry"
    PRICING_QUESTION = "pricing_question"
    SCHEDULE_CALL = "schedule_call"
    GENERAL_FAQ = "general_faq"
    COMPLAINT_OR_ESCALATION = "complaint_or_escalation"
    OFF_TOPIC = "off_topic"
    UNSAFE_OR_INJECTION = "unsafe_or_injection"


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Stable id for the browser session / lead")
    message: str
    buyer_name: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_phone: Optional[str] = None


class RetrievedProperty(BaseModel):
    id: str
    name: str
    city: str
    score: float


class ProposedSlot(BaseModel):
    consultant_id: str
    consultant_name: str
    slot_start: datetime
    slot_end: datetime
    match_score: float
    match_reasons: list[str]


class ChatResponse(BaseModel):
    session_id: str
    intent: Intent
    reply: str
    grounded: bool = Field(
        ..., description="True if the reply was generated strictly from retrieved context"
    )
    retrieved_properties: list[RetrievedProperty] = []
    proposed_slots: list[ProposedSlot] = []
    handoff_to_human: bool = False
    disclaimer: Optional[str] = None


class BookingRequest(BaseModel):
    session_id: str
    consultant_id: str
    slot_start: datetime
    buyer_name: str
    buyer_email: str
    buyer_phone: Optional[str] = None
    property_id: Optional[str] = None
    notes: Optional[str] = None


class BookingConfirmation(BaseModel):
    booking_id: str
    consultant_name: str
    consultant_email: str
    slot_start: datetime
    slot_end: datetime
    status: str


class LeadSummary(BaseModel):
    session_id: str
    buyer_name: Optional[str]
    buyer_email: Optional[str]
    buyer_phone: Optional[str]
    last_intent: Optional[str]
    interested_properties: list[str] = []
    preferences: dict = {}
    assigned_consultant: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class LeadDetail(LeadSummary):
    messages: list[dict] = []
