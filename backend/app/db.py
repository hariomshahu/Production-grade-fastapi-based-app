"""DynamoDB client and CRUD helpers. Uses IAM role on EC2 (no keys in code)."""
import os
import uuid
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "items")


def get_table():
    """Return DynamoDB table resource. Credentials from env or instance role."""
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(TABLE_NAME)


def create_item(name: str, description: Optional[str] = None) -> dict[str, Any]:
    """Insert a new item; generate id and created_at."""
    from datetime import datetime, timezone
    item_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    item = {
        "id": item_id,
        "name": name,
        "description": description or "",
        "created_at": created_at,
    }
    table = get_table()
    table.put_item(Item=item)
    return item


def get_item(item_id: str) -> Optional[dict[str, Any]]:
    """Get one item by id."""
    table = get_table()
    try:
        r = table.get_item(Key={"id": item_id})
        return r.get("Item")
    except ClientError:
        return None


def list_items(limit: int = 100, last_key: Optional[dict] = None) -> tuple[list[dict], Optional[dict]]:
    """Scan table with optional pagination. Returns (items, last_evaluated_key)."""
    table = get_table()
    params: dict = {"Limit": limit}
    if last_key:
        params["ExclusiveStartKey"] = last_key
    r = table.scan(**params)
    items = r.get("Items", [])
    last = r.get("LastEvaluatedKey")
    return items, last


def update_item(
    item_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Update item by id. Returns updated item or None if not found."""
    existing = get_item(item_id)
    if not existing:
        return None
    updates = []
    expr_names = {}
    expr_values = {}
    if name is not None:
        updates.append("#n = :n")
        expr_names["#n"] = "name"
        expr_values[":n"] = name
    if description is not None:
        updates.append("#d = :d")
        expr_names["#d"] = "description"
        expr_values[":d"] = description
    if not updates:
        return existing
    table = get_table()
    table.update_item(
        Key={"id": item_id},
        UpdateExpression="SET " + ", ".join(updates),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    return get_item(item_id)


def delete_item(item_id: str) -> bool:
    """Delete item by id. Returns True if deleted, False if not found."""
    existing = get_item(item_id)
    if not existing:
        return False
    table = get_table()
    table.delete_item(Key={"id": item_id})
    return True
