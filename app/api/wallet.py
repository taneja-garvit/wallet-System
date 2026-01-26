from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_id
from app.schemas.wallet import WalletResponse
from app.repositories.wallet_repo import get_wallet_by_user_id

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.get("", response_model=WalletResponse)
def get_wallet(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current user's wallet balance.
    User can only access their own wallet (enforced by JWT).
    """
    wallet = get_wallet_by_user_id(db, user_id)
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    return WalletResponse(
        wallet_id=wallet.id,
        balance=float(wallet.balance)
    )

