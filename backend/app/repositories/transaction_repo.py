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
    source_currency: str,
    target_currency: str,
    source_amount: Decimal,
    target_amount: Decimal,
    fx_rate: Decimal,
    fx_provider: str,
    fx_timestamp: datetime,
    status: str
) -> Transaction:
    """
    Create a new transaction record with FX metadata.
    
    All FX fields are required for audit trail:
    - fx_rate: Exchange rate used for conversion
    - fx_provider: Source of exchange rate (e.g., "STATIC")
    - fx_timestamp: When the rate was obtained
    
    This ensures deterministic reconciliation and auditability.
    """
    transaction = Transaction(
        idempotency_key=idempotency_key,
        sender_wallet_id=sender_wallet_id,
        receiver_wallet_id=receiver_wallet_id,
        source_currency=source_currency,
        target_currency=target_currency,
        source_amount=source_amount,
        target_amount=target_amount,
        fx_rate=fx_rate,
        fx_provider=fx_provider,
        fx_timestamp=fx_timestamp,
        status=status
    )
    db.add(transaction)
    db.flush()
    return transaction

def get_user_transactions(
    db: Session,
    wallet_ids: List[int],  # Changed to support multiple wallets per user
    limit: int,
    cursor_created_at: Optional[datetime] = None,
    cursor_id: Optional[int] = None
) -> list[Transaction]:
    """
    Get transactions for user's wallets with cursor pagination.
    Returns transactions where any of the user's wallets is sender or receiver.
    
    Args:
        wallet_ids: List of wallet IDs for the user (across all currencies)
        limit: Max number of transactions to return
        cursor_created_at: Cursor timestamp for pagination
        cursor_id: Cursor ID for pagination
    """
    query = db.query(Transaction).filter(
        or_(
            Transaction.sender_wallet_id.in_(wallet_ids),
            Transaction.receiver_wallet_id.in_(wallet_ids)
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

