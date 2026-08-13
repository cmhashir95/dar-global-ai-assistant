from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from app.models.database import Booking
from app.utils.llm_client import chat_completion_json

_CONSULTANTS_PATH = Path(__file__).resolve().parent.parent / "data" / "consultants.json"

WORK_START_HOUR = 9
WORK_END_HOUR = 18
SLOT_MINUTES = 30
LOOKAHEAD_DAYS = 7


def _load_consultants() -> list[dict]:
    with open(_CONSULTANTS_PATH) as f:
        return json.load(f)


def _seeded_bool(seed_str: str) -> bool:
    """Deterministic pseudo-randomness so a consultant's mock calendar looks
    the same across a server's lifetime instead of re-shuffling every call."""
    h = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    return h % 5 == 0  # ~20% of slots pre-booked, deterministic per slot


def generate_calendar(consultant_id: str, days: int = LOOKAHEAD_DAYS) -> list[dict]:
    """
    Mocks what a real integration (Google Calendar / Outlook Graph API) would
    return: a list of slots with free/busy status for the next N business
    days. Swapping this function's body for a real calendar API call is the
    only change needed to go from demo to production -- everything else in
    this module (matching, booking) is unaffected.
    """
    now = datetime.utcnow()
    slots = []
    day_cursor = now.date()
    days_added = 0
    day_offset = 0
    while days_added < days:
        day_offset += 1
        candidate_day = day_cursor + timedelta(days=day_offset)
        if candidate_day.weekday() >= 5:  # skip weekends
            continue
        days_added += 1
        cursor = datetime.combine(candidate_day, datetime.min.time()).replace(hour=WORK_START_HOUR)
        end_of_day = datetime.combine(candidate_day, datetime.min.time()).replace(hour=WORK_END_HOUR)
        while cursor < end_of_day:
            seed = f"{consultant_id}-{cursor.isoformat()}"
            slots.append(
                {
                    "start": cursor,
                    "end": cursor + timedelta(minutes=SLOT_MINUTES),
                    "available": not _seeded_bool(seed),
                }
            )
            cursor += timedelta(minutes=SLOT_MINUTES)
    return slots


@dataclass
class ConsultantMatch:
    consultant: dict
    expertise_score: float
    matched_tags: list[str]
    next_available_slots: list[dict]


def score_consultant(consultant: dict, interest_tags: list[str]) -> tuple[float, list[str]]:
    consultant_tags = set(consultant["expertise_tags"])
    interest_set = set(interest_tags)
    matched = sorted(consultant_tags & interest_set)
    if not interest_set:
        return 0.3, []  # no signal yet -> weak baseline score, availability breaks ties
    overlap_ratio = len(matched) / max(1, len(interest_set))
    # Blend expertise overlap with the consultant's track record (rating),
    # so among two equally-relevant consultants we prefer the stronger one.
    rating_component = (consultant.get("rating", 4.5) - 4.0) / 1.0  # ~0.0-1.0
    return round(0.75 * overlap_ratio + 0.25 * max(0.0, rating_component), 3), matched


def find_best_consultants(
    interest_tags: list[str], booked_slots_by_consultant: dict[str, set[str]], top_n: int = 3
) -> list[ConsultantMatch]:
    """
    Core of the "agentic" scheduling behaviour: for a lead's inferred
    interests (property type, city, budget tier -> tags), score all 3
    consultants by expertise fit, pull each one's live availability, and
    rank them so the best-fit + soonest-available consultant surfaces first.
    """
    consultants = _load_consultants()
    matches: list[ConsultantMatch] = []
    for c in consultants:
        score, matched_tags = score_consultant(c, interest_tags)
        calendar = generate_calendar(c["id"])
        already_booked = booked_slots_by_consultant.get(c["id"], set())
        free_slots = [
            s for s in calendar if s["available"] and s["start"].isoformat() not in already_booked
        ][:5]
        matches.append(
            ConsultantMatch(
                consultant=c, expertise_score=score, matched_tags=matched_tags, next_available_slots=free_slots
            )
        )

    # Rank by expertise score first, then by how soon their next free slot is.
    def sort_key(m: ConsultantMatch):
        soonest = m.next_available_slots[0]["start"] if m.next_available_slots else datetime.max
        return (-m.expertise_score, soonest)

    matches.sort(key=sort_key)
    return [m for m in matches if m.next_available_slots][:top_n]


_TAG_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "tags": {"type": "array", "items": {"type": "string"}},
        "city": {"type": "string"},
        "purpose": {"type": "string", "enum": ["investment", "end_use", "second_home", "unclear"]},
    },
    "required": ["tags", "city", "purpose"],
    "additionalProperties": False,
}

_TAG_EXTRACTION_PROMPT = """Extract structured buyer-interest tags from a real estate chat so we can match
them to the right sales consultant. Choose zero or more tags ONLY from this fixed vocabulary:
waterfront, off-plan, dubai, riyadh, uk-market, spain, mediterranean, branded-residences, serviced,
villas, golf, family, end-user, investment-yield, downtown, short-let, prime-london, ready,
ultra-luxury, second-home.
Also extract the city mentioned (or "" if none) and the likely purpose of the purchase."""


def extract_interest_tags(conversation_text: str) -> dict:
    messages = [
        {"role": "system", "content": _TAG_EXTRACTION_PROMPT},
        {"role": "user", "content": conversation_text},
    ]
    return chat_completion_json(
        messages, schema_name="interest_tags", json_schema=_TAG_EXTRACTION_SCHEMA, temperature=0
    )


def get_consultant(consultant_id: str) -> dict | None:
    for c in _load_consultants():
        if c["id"] == consultant_id:
            return c
    return None


def booked_slots_by_consultant(db_session) -> dict[str, set[str]]:
    booked: dict[str, set[str]] = {}
    for booking in db_session.query(Booking).filter(Booking.status == "confirmed").all():
        booked.setdefault(booking.consultant_id, set()).add(booking.slot_start.isoformat())
    return booked
