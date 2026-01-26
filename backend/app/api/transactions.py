from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user_id
from app.schemas.transaction import (
    TransferRequest,
    TransferResponse,
    TransactionHistoryResponse
)
from app.services.transaction_service import transfer_money, get_transaction_history
from app.utils.idempotency import get_idempotency_key

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/transfer", response_model=TransferResponse)
def transfer(
    request: TransferRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key)
):
    """
    Transfer money from current user to another user with multi-currency support.
    
    Features:
    - Multi-currency support with automatic FX conversion
    - Idempotent (same key = same result)
    - ACID guarantees
    - Deadlock prevention
    - Balance validation
    - Immutable audit trail with FX metadata
    
    Interview line:
    "Sender identity is derived from JWT, never from request payload."
    "FX rate used for conversion is persisted with the transaction 
     to ensure auditability and deterministic reconciliation."
    """
    try:
        result = transfer_money(
            db=db,
            sender_user_id=user_id,
            receiver_user_id=request.receiver_user_id,
            source_currency=request.source_currency,
            target_currency=request.target_currency,
            amount=request.amount,
            idempotency_key=idempotency_key
        )
        
        # Check for errors in result
        if "error" in result:
            if result["error"] == "INSUFFICIENT_BALANCE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="INSUFFICIENT_BALANCE"
                )
            elif result["error"] == "IDEMPOTENCY_KEY_CONFLICT":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="IDEMPOTENCY_KEY_CONFLICT"
                )
        
        return TransferResponse(
            transaction_id=result["transaction_id"],
            status=result["status"],
            source_amount=result["source_amount"],
            source_currency=result["source_currency"],
            target_amount=result["target_amount"],
            target_currency=result["target_currency"],
            fx_rate=result["fx_rate"]
        )
        
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "IDEMPOTENCY_KEY_CONFLICT":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="IDEMPOTENCY_KEY_CONFLICT"
            )
        elif "deadlock" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transaction failed due to deadlock. Please retry."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("", response_model=TransactionHistoryResponse)
def get_transactions(
    limit: int = 20,
    cursor: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for current user with cursor pagination.
    
    Returns transactions where user is either sender or receiver.
    Uses cursor pagination for stable, efficient pagination.
    """
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        result = get_transaction_history(
            db=db,
            user_id=user_id,
            limit=limit,
            cursor=cursor
        )
        
        return TransactionHistoryResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

