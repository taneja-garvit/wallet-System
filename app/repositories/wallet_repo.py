from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.wallet import Wallet

def create_wallet(db: Session, user_id: int):
    wallet = Wallet(user_id=user_id, balance=0)
    db.add(wallet)
    return wallet

def lock_wallet(db: Session, wallet_id: int):
    return db.execute(
        select(Wallet).where(Wallet.id == wallet_id).with_for_update() 
    ).scalar_one()
