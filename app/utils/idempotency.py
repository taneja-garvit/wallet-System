from fastapi import Header, HTTPException, status
from typing import Optional
import uuid

def get_idempotency_key(idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")) -> str:
    """
    Extract and validate idempotency key from header.
    Raises 400 if missing or invalid.
    """
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required"
        )
    
    # Validate UUID format
    try:
        uuid.UUID(idempotency_key)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must be a valid UUID"
        )
    
    return idempotency_key

