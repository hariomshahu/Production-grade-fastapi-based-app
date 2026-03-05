"""CRUD API for Items."""
from fastapi import APIRouter, HTTPException, Query

from app.models import Item, ItemCreate, ItemUpdate
from app import db

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=Item)
def create_item(payload: ItemCreate):
    """Create a new item."""
    row = db.create_item(name=payload.name, description=payload.description)
    return Item(
        id=row["id"],
        name=row["name"],
        description=row.get("description") or None,
        created_at=row["created_at"],
    )


@router.get("", response_model=dict)
def list_items(
    limit: int = Query(100, ge=1, le=100),
    last_id: str | None = Query(None, alias="lastEvaluatedKey"),
):
    """List items with optional pagination."""
    last_key = {"id": last_id} if last_id else None
    items, last_eval = db.list_items(limit=limit, last_key=last_key)
    result = {
        "items": [
            Item(
                id=r["id"],
                name=r["name"],
                description=r.get("description") or None,
                created_at=r["created_at"],
            )
            for r in items
        ],
    }
    if last_eval:
        result["lastEvaluatedKey"] = last_eval.get("id")
    return result


@router.get("/{item_id}", response_model=Item)
def get_item(item_id: str):
    """Get one item by id."""
    row = db.get_item(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(
        id=row["id"],
        name=row["name"],
        description=row.get("description") or None,
        created_at=row["created_at"],
    )


@router.put("/{item_id}", response_model=Item)
def update_item(item_id: str, payload: ItemUpdate):
    """Full update of an item."""
    row = db.update_item(
        item_id,
        name=payload.name,
        description=payload.description,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(
        id=row["id"],
        name=row["name"],
        description=row.get("description") or None,
        created_at=row["created_at"],
    )


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: str):
    """Delete an item."""
    if not db.delete_item(item_id):
        raise HTTPException(status_code=404, detail="Item not found")
