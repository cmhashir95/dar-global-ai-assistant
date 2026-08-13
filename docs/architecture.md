# Architecture

## System overview

```
                     ┌──────────────────────┐
                     │   Website (React)     │  buyer-facing, public
                     │  frontend/             │
                     └──────────┬────────────┘
                                │ REST (fetch)
                     ┌──────────▼────────────┐
                     │  Consultant Dashboard  │  internal tool
                     │  consultant-dashboard/ │
                     └──────────┬────────────┘
                                │ REST (fetch)
┌───────────────────────────────▼───────────────────────────────┐
│                        FastAPI backend                          │
│                                                                   │
│  /api/chat        -> orchestrator.handle_chat_turn               │
│  /api/properties   -> vector_store (catalog read)                │
│  /api/consultants  -> scheduler_agent (availability, booking)    │
│  /api/leads         -> SQLite (dashboard read model)             │
│                                                                   │
│  ┌────────────────────────── orchestrator ──────────────────┐   │
│  │  1. intent_classifier.classify_intent()                   │   │
│  │  2. guardrails.gate_response()      <- hard stop for       │   │
│  │     off-topic / injection / complaint, no LLM call at all  │   │
│  │  3. route by intent:                                        │  │
│  │       property_inquiry/pricing -> rag_engine                │  │
│  │       schedule_call            -> scheduler_agent            │ │
│  │       greeting/general_faq     -> fixed/templated reply      │ │
│  │  4. guardrails.check_grounding() on every RAG reply          │ │
│  │  5. persist Lead + Message rows for the dashboard             ││
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

## Why each piece exists

### 1. Intent classification is a separate, first-class step

`app/core/intent_classifier.py` runs **before** any generation happens. It's a two-layer
design:

- **Rule layer** (regex/keyword) catches the cases that matter most to get right and where a
  false negative is costly: prompt-injection attempts, off-topic chit-chat, and clear scheduling
  requests. It's instant and has zero hallucination risk because it's not a model at all.
- **LLM layer** only runs on genuinely ambiguous messages, and even then it's constrained to a
  fixed JSON schema (`response_format: json_schema` with `strict: true`), so the output is always
  exactly one of a known set of enum values -- never free text that needs fragile parsing.

This is what the brief calls a "strong intent identifier": every single message is screened,
classification happens before the model is allowed to freely respond, and the riskiest intents
(`off_topic`, `unsafe_or_injection`) are hard-gated (see below) rather than merely "discouraged"
by a system prompt.

### 2. Guardrails are enforced in code, not just prompted

`app/core/guardrails.py` has two halves:

- **Pre-generation gate** (`gate_response`): for `off_topic`, `unsafe_or_injection`, and
  `complaint_or_escalation`, the reply is a fixed, reviewed string. The LLM is never called for
  these turns. This is a much stronger guarantee against drift/jailbreaks than "please stay on
  topic" in a system prompt, because there is nothing generative in the loop that could go wrong.
- **Post-generation check** (`check_grounding`): every RAG reply is scanned for property IDs it
  cites. If the model mentions an ID that wasn't in the retrieved context (or makes a specific
  price/spec claim with no retrieved properties at all), the reply is discarded and replaced with
  a safe fallback that offers to connect the visitor with a human instead of guessing. This is the
  "don't hallucinate" requirement enforced structurally rather than hoped for.

### 3. RAG is scoped, cited, and fails closed

`app/core/rag_engine.py` retrieves the top matching properties from a Chroma vector store
(`app/utils/vector_store.py`, embeddings via local `sentence-transformers` by default -- no
external API dependency required to run the demo), builds an explicit CONTEXT block, and instructs
the model to answer **only** from that block and cite property IDs. Low temperature (0.2) is used
throughout for the same reason: this is a task-grounded assistant, not a creative one.

### 4. Scheduling is a small agent, not a form

`app/core/scheduler_agent.py` is what makes the booking flow "agentic" rather than a static
contact form:

1. It extracts structured interest tags from the conversation (city, property type, budget tier,
   purpose) via a schema-constrained LLM call.
2. It scores all three consultants by tag overlap with their stated expertise, blended with their
   rating, and pulls each one's live calendar (mocked here, but the function signature is exactly
   what you'd swap for a real Google Calendar / Outlook Graph API call).
3. It ranks by best-fit-then-soonest and proposes concrete slots back to the user.
4. Booking re-validates slot availability server-side at write time (`/api/consultants/book`) to
   avoid a race where two visitors book the same slot.

### 5. Everything a consultant needs is captured automatically

Every turn is persisted (`app/models/database.py`: `Lead`, `Message`, `Booking`). The dashboard
(`consultant-dashboard/`) reads this directly -- no separate CRM integration needed for the demo.
A `Lead` accumulates buyer contact info (as soon as it's given), which properties they showed
interest in, inferred preferences/tags, assigned consultant, and full transcript, so a human
consultant opening a lead has full context before the first call.

## Data flow for a single "book a call" turn

1. Visitor: *"I want a 3-bedroom villa in Dubai, can someone call me?"*
2. Rule layer matches `schedule` keyword -> `Intent.SCHEDULE_CALL` (no LLM call needed for intent).
3. `scheduler_agent.extract_interest_tags()` -> `{"tags": ["villas", "dubai", "family"], "city": "Dubai", ...}`.
4. `find_best_consultants()` scores Leila Haddad, Omar Al-Rashid, Sophie Bennett against those tags
   and each consultant's live (mock) calendar; Leila/Omar rank highest for `dubai`/`villas`.
5. Two upcoming slots per top consultant are returned to the widget as clickable options.
6. Visitor picks a slot -> `BookingConfirm` collects name/email -> `POST /api/consultants/book`
   re-checks the slot is still free -> `Booking` row created, `Lead.status = "scheduled"`.
7. The consultant dashboard shows the new lead immediately (polling every 8s) with full transcript
   and the reason it was matched to that consultant.

## Swapping mocked pieces for production

| Mocked in this repo | Real integration point |
|---|---|
| `scheduler_agent.generate_calendar()` | Google Calendar / Outlook Graph API free-busy query |
| SQLite | Postgres (just change `DATABASE_URL`) |
| Local `sentence-transformers` embeddings | `EMBEDDING_MODE=openai` (already supported) or any embedding API |
| `properties.json` | A CMS/PIM export job that re-runs the Chroma indexing step |
| Booking confirmation (log only) | Email/SMS provider (SendGrid, Twilio) + calendar invite (.ics) |
