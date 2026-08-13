from __future__ import annotations

from fastapi import APIRouter

from app.utils.vector_store import get_vector_store

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("")
def list_properties():
    return get_vector_store().all_properties()


@router.get("/{property_id}")
def get_property(property_id: str):
    return get_vector_store().get_property(property_id)
