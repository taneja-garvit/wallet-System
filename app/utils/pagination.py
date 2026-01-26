import base64
import json
from typing import Optional
from datetime import datetime

def encode_cursor(created_at: datetime, transaction_id: int) -> str:
    """Encode cursor as base64 JSON"""
    cursor_data = {
        "created_at": created_at.isoformat(),
        "transaction_id": transaction_id
    }
    json_str = json.dumps(cursor_data)
    return base64.b64encode(json_str.encode()).decode()

def decode_cursor(cursor: str) -> tuple[datetime, int]:
    """Decode cursor from base64 JSON"""
    try:
        json_str = base64.b64decode(cursor.encode()).decode()
        cursor_data = json.loads(json_str)
        created_at = datetime.fromisoformat(cursor_data["created_at"])
        transaction_id = int(cursor_data["transaction_id"])
        return created_at, transaction_id
    except (ValueError, KeyError, json.JSONDecodeError):
        raise ValueError("Invalid cursor format")

