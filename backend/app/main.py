from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, consultants, leads, properties
from app.config import settings
from app.models.database import init_db

app = FastAPI(
    title="Dar Global AI Assistant",
    description="Agentic RAG chatbot for property inquiries and consultant scheduling.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "env": settings.app_env}


app.include_router(chat.router)
app.include_router(consultants.router)
app.include_router(leads.router)
app.include_router(properties.router)
