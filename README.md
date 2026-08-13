# Dar Global AI Assistant

An agentic AI chatbot for a real estate company, built as a portfolio project. It answers property
questions with retrieval-augmented generation grounded in a property catalog, and can autonomously
match and book a visitor with the best-fit sales consultant based on live availability and
expertise — with a strong intent classifier and structural guardrails to keep it on-task and
non-hallucinating.

> **Note:** all property, consultant, and pricing data in this repo is synthetic demo data. This
> is not affiliated with or endorsed by the real Dar Global.

## What's inside

```
dar-global-ai-assistant/
├── backend/                  FastAPI app: RAG, intent classifier, guardrails, scheduling agent
├── frontend/                 Buyer-facing website with embedded chat widget (React + Vite)
├── consultant-dashboard/     Internal tool: leads, transcripts, preferences (React + Vite)
├── docker-compose.yml        Run all three together
└── docs/architecture.md      System design + rationale for every guardrail
```

## Features

- **RAG over the property catalog** — Chroma vector store, local embeddings by default (no API
  key required just to search), every answer cites property IDs so it can be checked against what
  was retrieved.
- **Agentic scheduling** — extracts buyer intent/preferences, scores 3 sales consultants by
  expertise fit + live calendar availability, proposes concrete slots, books with a server-side
  race check.
- **Strong intent screening** — every message is classified (greeting / property inquiry /
  pricing / schedule call / FAQ / complaint / off-topic / injection attempt) before anything is
  generated, via a fast rule layer plus a schema-constrained LLM fallback.
- **Guardrails against drift & hallucination** — off-topic and prompt-injection intents never
  reach the generator at all (fixed replies only); every RAG answer is checked post-generation
  against what was actually retrieved and discarded in favor of a safe fallback if it isn't
  grounded. See [`docs/architecture.md`](docs/architecture.md) for the full rationale.
- **Consultant dashboard** — every conversation, inferred buyer preferences, and booking is
  captured automatically and visible to the sales team in near real time.

## Quick start (local, no Docker)

Requires Python 3.11+, Node 20+, and an OpenAI API key (or any OpenAI-compatible endpoint).

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env and set OPENAI_API_KEY
uvicorn app.main:app --reload
```

The first run downloads a small local embedding model (`all-MiniLM-L6-v2`) and indexes the demo
catalog into `./chroma_store`. API docs at `http://localhost:8000/docs`.

### 2. Website (buyer-facing)

```bash
cd frontend
npm install
cp .env.example .env        # defaults to http://localhost:8000, fine for local dev
npm run dev
```

Visit `http://localhost:5173`.

### 3. Consultant dashboard

```bash
cd consultant-dashboard
npm install
cp .env.example .env
npm run dev
```

Visit `http://localhost:5174`.

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env   # set OPENAI_API_KEY
docker compose up --build
```

- Website: `http://localhost:4173`
- Consultant dashboard: `http://localhost:4174`
- API: `http://localhost:8000`

## Running the tests

```bash
cd backend
pytest
```

The included tests cover the rule-based intent screen and the grounding/anti-hallucination check —
both are pure functions with no network calls, so they run without an API key.

## Deploying for free

This is a standard 3-service app, so any of the usual free/low-cost tiers work:

- **Backend**: [Render](https://render.com) or [Railway](https://railway.app) free web service
  (Dockerfile included), or [Fly.io](https://fly.io).
- **Frontend / dashboard**: [Vercel](https://vercel.com) or [Netlify](https://netlify.com) — point
  each at its subfolder, set `VITE_API_BASE_URL` to your deployed backend URL as a build-time env
  var.
- **Database**: SQLite file is fine for a demo; swap `DATABASE_URL` for a managed Postgres (e.g.
  Supabase/Neon free tier) for anything longer-lived.

## Configuration reference

See [`backend/.env.example`](backend/.env.example) for every backend setting. The two you're most
likely to change:

- `EMBEDDING_MODE` — `local` (default, free, offline `sentence-transformers`) or `openai`.
- `CHAT_MODEL` — any OpenAI-compatible chat model id.

## License

MIT — see [`LICENSE`](LICENSE). Demo data only; not real property or pricing information.
