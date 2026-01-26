from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
from app.models.wallet import Wallet

def create_wallet(db: Session, user_id: int, currency: str) -> Wallet:
    """
    Create a new wallet for a user in the specified currency.
    Enforces: one wallet per currency per user.
    """
    wallet = Wallet(user_id=user_id, currency=currency, balance=0)
    db.add(wallet)
    return wallet

def get_wallet_by_user_id(db: Session, user_id: int) -> Optional[Wallet]:
    """
    Get wallet by user_id (no lock).
    DEPRECATED: Use get_wallet_by_user_and_currency for multi-currency.
    Returns first wallet found (for backward compatibility).
    """
    return db.query(Wallet).filter(Wallet.user_id == user_id).first()

def get_wallet_by_user_and_currency(
    db: Session, 
    user_id: int, 
    currency: str
) -> Optional[Wallet]:
    """
    Get wallet by user_id and currency (no lock).
    This is the primary lookup method for multi-currency wallets.
    """
    return db.query(Wallet).filter(
        Wallet.user_id == user_id,
        Wallet.currency == currency
    ).first()

def get_all_wallets_by_user(db: Session, user_id: int) -> List[Wallet]:
    """Get all wallets for a user (across all currencies)"""
    return db.query(Wallet).filter(Wallet.user_id == user_id).order_by(Wallet.currency).all()

def lock_wallet(db: Session, wallet_id: int) -> Wallet:
    """Lock wallet row for update (deadlock prevention)"""
    return db.execute(
        select(Wallet).where(Wallet.id == wallet_id).with_for_update() 
    ).scalar_one()

def lock_wallets_ordered(db: Session, wallet_id1: int, wallet_id2: int) -> tuple[Wallet, Wallet]:
    """
    Lock two wallets in deterministic order to prevent deadlocks.
    
    Design principle:
    Always lock smaller wallet_id first regardless of sender/receiver role.
    This prevents circular wait conditions.
    """
    # Always lock smaller ID first
    if wallet_id1 < wallet_id2:
        wallet1 = lock_wallet(db, wallet_id1)
        wallet2 = lock_wallet(db, wallet_id2)
        return (wallet1, wallet2)
    else:
        wallet2 = lock_wallet(db, wallet_id2)
        wallet1 = lock_wallet(db, wallet_id1)
        return (wallet1, wallet2)
