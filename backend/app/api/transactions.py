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
    Transfer money from current user to another user.
    
    Features:
    - Idempotent (same key = same result)
    - ACID guarantees
    - Deadlock prevention
    - Balance validation
    """
    try:
        result = transfer_money(
            db=db,
            sender_user_id=user_id,
            receiver_user_id=request.receiver_user_id,
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
            amount=result["amount"]
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

