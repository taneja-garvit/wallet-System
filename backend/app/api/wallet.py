from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_id
from app.schemas.wallet import WalletResponse, UpdateWalletNameRequest
from app.repositories.wallet_repo import get_wallet_by_user_id, update_wallet_name

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.get("", response_model=WalletResponse)
def get_wallet(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current user's wallet balance and details.
    Single currency system (INR).
    """
    wallet = get_wallet_by_user_id(db, user_id)
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    return WalletResponse(
        wallet_id=wallet.id,
        name=wallet.name,
        balance=float(wallet.balance)
    )

@router.patch("/name", response_model=WalletResponse)
def update_name(
    request: UpdateWalletNameRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update wallet name.
    User can customize their wallet name.
    """
    wallet = get_wallet_by_user_id(db, user_id)
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    try:
        updated_wallet = update_wallet_name(db, wallet.id, request.name)
        db.commit()
        
        return WalletResponse(
            wallet_id=updated_wallet.id,
            name=updated_wallet.name,
            balance=float(updated_wallet.balance)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
