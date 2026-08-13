from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import create_engine, Column, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


class Lead(Base):
    """
    A buyer/prospect. One row per chat session. This is what the consultant
    dashboard reads: contact details, inferred preferences, which properties
    they showed interest in, and whether they've been matched/booked with a
    consultant.
    """

    __tablename__ = "leads"

    session_id = Column(String, primary_key=True)
    buyer_name = Column(String, nullable=True)
    buyer_email = Column(String, nullable=True)
    buyer_phone = Column(String, nullable=True)
    last_intent = Column(String, nullable=True)
    interested_properties = Column(Text, default="[]")  # JSON list of property ids
    preferences = Column(Text, default="{}")  # JSON dict: budget, bedrooms, city, purpose...
    assigned_consultant = Column(String, nullable=True)
    status = Column(String, default="new")  # new | qualifying | scheduled | escalated | closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="lead", cascade="all, delete-orphan")

    def interested_properties_list(self) -> list[str]:
        return json.loads(self.interested_properties or "[]")

    def preferences_dict(self) -> dict:
        return json.loads(self.preferences or "{}")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: new_id("MSG"))
    session_id = Column(String, ForeignKey("leads.session_id"))
    role = Column(String)  # user | assistant | system
    content = Column(Text)
    intent = Column(String, nullable=True)
    grounded = Column(String, nullable=True)  # "true"/"false" as string for sqlite simplicity
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="messages")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=lambda: new_id("BOOK"))
    session_id = Column(String, ForeignKey("leads.session_id"))
    consultant_id = Column(String)
    consultant_name = Column(String)
    property_id = Column(String, nullable=True)
    slot_start = Column(DateTime)
    slot_end = Column(DateTime)
    match_score = Column(Float, default=0.0)
    status = Column(String, default="confirmed")  # confirmed | cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="bookings")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
