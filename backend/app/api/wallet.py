from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db, get_current_user_id
from app.schemas.wallet import WalletResponse, WalletListResponse, CreateWalletRequest
from app.repositories.wallet_repo import (
    get_wallet_by_user_and_currency,
    get_all_wallets_by_user,
    create_wallet
)
from app.services.fx_service import get_fx_service

router = APIRouter(prefix="/wallets", tags=["wallets"])

@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def create_user_wallet(
    request: CreateWalletRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new wallet in the specified currency.
    
    Rules:
    - One wallet per currency per user
    - Duplicate currency -> 409 Conflict
    - Only supported currencies allowed
    """
    # Validate currency is supported
    fx_service = get_fx_service()
    if not fx_service.is_currency_supported(request.currency):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Currency {request.currency} is not supported"
        )
    
    # Check if wallet already exists
    existing = get_wallet_by_user_and_currency(db, user_id, request.currency)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Wallet for currency {request.currency} already exists"
        )
    
    try:
        # Create new wallet
        wallet = create_wallet(db, user_id, request.currency)
        db.commit()
        db.refresh(wallet)
        
        return WalletResponse(
            wallet_id=wallet.id,
            currency=wallet.currency,
            balance=float(wallet.balance)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Wallet for currency {request.currency} already exists"
        )

@router.get("", response_model=WalletListResponse)
def get_wallets(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get all wallets for the current user (across all currencies).
    User can only access their own wallets (enforced by JWT).
    
    Returns:
        List of wallets sorted by currency
    """
    wallets = get_all_wallets_by_user(db, user_id)
    
    return WalletListResponse(
        wallets=[
            WalletResponse(
                wallet_id=w.id,
                currency=w.currency,
                balance=float(w.balance)
            )
            for w in wallets
        ]
    )

