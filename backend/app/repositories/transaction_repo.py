from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.models.transaction import Transaction

def get_transaction_by_idempotency_key(db: Session, idempotency_key: str) -> Optional[Transaction]:
    """Check if transaction with idempotency key already exists"""
    return db.query(Transaction).filter(Transaction.idempotency_key == idempotency_key).first()

def create_transaction(
    db: Session,
    idempotency_key: str,
    sender_wallet_id: int,
    receiver_wallet_id: int,
    amount: Decimal,
    status: str
) -> Transaction:
    """Create a new transaction record. Single currency (INR)."""
    transaction = Transaction(
        idempotency_key=idempotency_key,
        sender_wallet_id=sender_wallet_id,
        receiver_wallet_id=receiver_wallet_id,
        amount=amount,
        status=status
    )
    db.add(transaction)
    db.flush()
    return transaction

def get_user_transactions(
    db: Session,
    wallet_id: int,  # Single wallet per user
    limit: int,
    cursor_created_at: Optional[datetime] = None,
    cursor_id: Optional[int] = None
) -> list[Transaction]:
    """
    Get transactions for user's wallet with cursor pagination.
    Returns transactions where wallet is sender or receiver.
    """
    query = db.query(Transaction).filter(
        or_(
            Transaction.sender_wallet_id == wallet_id,
            Transaction.receiver_wallet_id == wallet_id
        )
    )
    
    # Apply cursor if provided
    if cursor_created_at is not None and cursor_id is not None:
        query = query.filter(
            or_(
                Transaction.created_at < cursor_created_at,
                and_(
                    Transaction.created_at == cursor_created_at,
                    Transaction.id < cursor_id
                )
            )
        )
    
    # Order by created_at DESC, id DESC for deterministic pagination
    query = query.order_by(Transaction.created_at.desc(), Transaction.id.desc())
    
    # Limit results
    return query.limit(limit).all()

