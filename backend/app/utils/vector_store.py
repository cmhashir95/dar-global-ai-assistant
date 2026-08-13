from __future__ import annotations

import json
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from app.config import settings

_PROPERTIES_PATH = Path(__file__).resolve().parent.parent / "data" / "properties.json"
_COLLECTION_NAME = "dar_global_properties"


def _get_embedding_function():
    if settings.embedding_mode == "openai":
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            api_base=settings.openai_base_url,
            model_name=settings.openai_embedding_model,
        )
    # Default: local, free, offline sentence-transformers model. Good enough
    # for a catalog of a few thousand listings and means the RAG step never
    # depends on an external API being reachable.
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


def _property_to_document(p: dict) -> str:
    return (
        f"{p['name']} ({p['id']}) is a {p['type']} in {p['community']}, {p['city']}, {p['country']}. "
        f"Status: {p['status']}, handover: {p['handover']}. Bedrooms: {p['bedrooms']}. "
        f"Price range: ${p['price_from_usd']:,} to ${p['price_to_usd']:,} USD. "
        f"Size: {p['size_sqft'][0]}-{p['size_sqft'][1]} sqft. "
        f"Amenities: {', '.join(p['amenities'])}. Payment plan: {p['payment_plan']}. "
        f"{p['highlights']}"
    )


class PropertyVectorStore:
    def __init__(self):
        os.makedirs(settings.vector_db_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=settings.vector_db_dir)
        self._ef = _get_embedding_function()
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME, embedding_function=self._ef
        )
        self._properties_by_id: dict[str, dict] = {}
        self._load_properties()
        self._ensure_indexed()

    def _load_properties(self) -> None:
        with open(_PROPERTIES_PATH) as f:
            properties = json.load(f)
        self._properties_by_id = {p["id"]: p for p in properties}

    def _ensure_indexed(self) -> None:
        existing_ids = set(self._collection.get(include=[])["ids"])
        all_ids = set(self._properties_by_id.keys())
        missing = all_ids - existing_ids
        if not missing:
            return
        docs, ids, metadatas = [], [], []
        for pid in missing:
            p = self._properties_by_id[pid]
            docs.append(_property_to_document(p))
            ids.append(pid)
            metadatas.append(
                {
                    "city": p["city"],
                    "country": p["country"],
                    "status": p["status"],
                    "min_bedrooms": min(p["bedrooms"]),
                    "max_bedrooms": max(p["bedrooms"]),
                    "price_from_usd": p["price_from_usd"],
                    "price_to_usd": p["price_to_usd"],
                    "expertise_tags": ",".join(p["expertise_tags"]),
                }
            )
        self._collection.add(documents=docs, ids=ids, metadatas=metadatas)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Returns a list of {property (full dict), score} sorted best-first."""
        result = self._collection.query(query_texts=[query], n_results=min(top_k, len(self._properties_by_id)))
        hits = []
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for pid, dist in zip(ids, distances):
            # Chroma returns a distance (lower = closer); convert to an
            # intuitive 0-1 similarity score for the API/UI layer.
            score = max(0.0, 1.0 - dist)
            hits.append({"property": self._properties_by_id[pid], "score": round(score, 3)})
        return hits

    def get_property(self, property_id: str) -> dict | None:
        return self._properties_by_id.get(property_id)

    def all_properties(self) -> list[dict]:
        return list(self._properties_by_id.values())


_store: PropertyVectorStore | None = None


def get_vector_store() -> PropertyVectorStore:
    global _store
    if _store is None:
        _store = PropertyVectorStore()
    return _store
