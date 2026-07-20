from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.wallet import Wallet

def create_wallet(db: Session, user_id: int, name: str = "My Wallet") -> Wallet:
    """
    Create a new wallet for a user.
    Single currency system (INR).
    """
    wallet = Wallet(user_id=user_id, name=name, balance=0)
    db.add(wallet)
    return wallet

def get_wallet_by_user_id(db: Session, user_id: int) -> Optional[Wallet]:
    """Get wallet by user_id (no lock). One wallet per user."""
    return db.query(Wallet).filter(Wallet.user_id == user_id).first()

def update_wallet_name(db: Session, wallet_id: int, name: str) -> Wallet:
    """Update wallet name"""
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if wallet:
        wallet.name = name
        db.flush()
    return wallet

def lock_wallet_by_user_id(db: Session, user_id: int) -> Optional[Wallet]:
    """Lock wallet row by user_id for update (deadlock prevention)"""
    return db.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update() 
    ).scalar_one_or_none()

def lock_wallets_ordered_by_user_id(db: Session, user_id1: int, user_id2: int) -> tuple[Optional[Wallet], Optional[Wallet]]:
    """
    Lock two wallets by user_id in deterministic order to prevent deadlocks.
    
    Design principle:
    Always lock smaller user_id first regardless of sender/receiver role.
    This prevents circular wait conditions.
    """
    # Always lock smaller ID first
    if user_id1 < user_id2:
        wallet1 = lock_wallet_by_user_id(db, user_id1)
        wallet2 = lock_wallet_by_user_id(db, user_id2)
        return (wallet1, wallet2)
    else:
        wallet2 = lock_wallet_by_user_id(db, user_id2)
        wallet1 = lock_wallet_by_user_id(db, user_id1)
        return (wallet1, wallet2)
