from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from typing import Optional
from decimal import Decimal

from app.repositories.wallet_repo import get_wallet_by_user_id, lock_wallets_ordered
from app.repositories.transaction_repo import (
    get_transaction_by_idempotency_key,
    create_transaction,
    get_user_transactions
)
from app.utils.pagination import encode_cursor, decode_cursor
from app.models.transaction import Transaction

# Transaction status constants
STATUS_PENDING = "PENDING"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"

def transfer_money(
    db: Session,
    sender_user_id: int,
    receiver_user_id: int,
    amount: float,
    idempotency_key: str
) -> dict:
    """
    Transfer money between wallets with ACID guarantees.
    
    Flow:
    1. Check idempotency (return existing if found)
    2. Validate inputs
    3. Start transaction
    4. Lock wallets in deterministic order (deadlock prevention)
    5. Check balance
    6. Apply changes
    7. Create transaction record
    8. Commit
    
    Returns transaction result or raises exception.
    """
    # Step 1: Idempotency check (BEFORE acquiring locks)
    existing_transaction = get_transaction_by_idempotency_key(db, idempotency_key)
    if existing_transaction:
        # Validate that payload matches existing transaction
        # Get wallet IDs for comparison
        sender_wallet = get_wallet_by_user_id(db, sender_user_id)
        receiver_wallet = get_wallet_by_user_id(db, receiver_user_id)
        
        if not sender_wallet or not receiver_wallet:
            raise ValueError("Wallet not found")
        
        # Check if payload matches
        if (existing_transaction.sender_wallet_id != sender_wallet.id or
            existing_transaction.receiver_wallet_id != receiver_wallet.id or
            existing_transaction.amount != Decimal(str(amount))):
            # Same key but different payload - conflict!
            raise ValueError("IDEMPOTENCY_KEY_CONFLICT")
        
        # Return existing result - same idempotency key = same response
        return {
            "transaction_id": existing_transaction.id,
            "status": existing_transaction.status,
            "amount": float(existing_transaction.amount)
        }
    
    # Step 2: Validate inputs
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    if sender_user_id == receiver_user_id:
        raise ValueError("Sender and receiver cannot be the same")
    
    # Step 3: Get wallet IDs
    sender_wallet = get_wallet_by_user_id(db, sender_user_id)
    receiver_wallet = get_wallet_by_user_id(db, receiver_user_id)
    
    if not sender_wallet:
        raise ValueError("Sender wallet not found")
    if not receiver_wallet:
        raise ValueError("Receiver wallet not found")
    
    sender_wallet_id = sender_wallet.id
    receiver_wallet_id = receiver_wallet.id
    
    # Step 4: Start DB transaction (everything below is atomic)
    try:
        # Step 5: Lock wallets in deterministic order (deadlock prevention)
        # Always lock smaller wallet_id first
        sender_wallet_locked, receiver_wallet_locked = lock_wallets_ordered(
            db, sender_wallet_id, receiver_wallet_id
        )
        
        # Step 6: Balance check (fail early)
        if sender_wallet_locked.balance < Decimal(str(amount)):
            # Create FAILED transaction record
            transaction = create_transaction(
                db=db,
                idempotency_key=idempotency_key,
                sender_wallet_id=sender_wallet_id,
                receiver_wallet_id=receiver_wallet_id,
                amount=amount,
                status=STATUS_FAILED
            )
            db.commit()
            return {
                "transaction_id": transaction.id,
                "status": STATUS_FAILED,
                "amount": amount,
                "error": "INSUFFICIENT_BALANCE"
            }
        
        # Step 7: Apply balance changes
        sender_wallet_locked.balance -= Decimal(str(amount))
        receiver_wallet_locked.balance += Decimal(str(amount))
        
        # Step 8: Create transaction record
        transaction = create_transaction(
            db=db,
            idempotency_key=idempotency_key,
            sender_wallet_id=sender_wallet_id,
            receiver_wallet_id=receiver_wallet_id,
            amount=amount,
            status=STATUS_SUCCESS
        )
        
        # Step 9: Commit (atomic)
        db.commit()
        
        return {
            "transaction_id": transaction.id,
            "status": STATUS_SUCCESS,
            "amount": amount
        }
        
    except IntegrityError as e:
        # Handle duplicate idempotency key (race condition)
        db.rollback()
        # Check if another request created it
        existing = get_transaction_by_idempotency_key(db, idempotency_key)
        if existing:
            return {
                "transaction_id": existing.id,
                "status": existing.status,
                "amount": float(existing.amount)
            }
        # If different payload, raise conflict
        raise ValueError("IDEMPOTENCY_KEY_CONFLICT")
    
    except OperationalError as e:
        # Handle deadlocks - rollback and let caller retry
        db.rollback()
        # Could implement retry logic here, but for now raise
        raise ValueError("Transaction failed due to deadlock. Please retry.")
    
    except Exception as e:
        # Any other error - rollback
        db.rollback()
        raise

def get_transaction_history(
    db: Session,
    user_id: int,
    limit: int = 20,
    cursor: Optional[str] = None
) -> dict:
    """
    Get transaction history for a user with cursor pagination.
    
    Returns transactions where user is either sender or receiver.
    """
    # Get user's wallet
    wallet = get_wallet_by_user_id(db, user_id)
    if not wallet:
        raise ValueError("Wallet not found")
    
    # Decode cursor if provided
    cursor_created_at = None
    cursor_id = None
    if cursor:
        try:
            cursor_created_at, cursor_id = decode_cursor(cursor)
        except ValueError:
            raise ValueError("Invalid cursor format")
    
    # Get transactions
    transactions = get_user_transactions(
        db=db,
        wallet_id=wallet.id,
        limit=limit + 1,  # Fetch one extra to check if there's more
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id
    )
    
    # Check if there's a next page
    has_next = len(transactions) > limit
    if has_next:
        transactions = transactions[:limit]
    
    # Format response
    result = []
    for tx in transactions:
        # Determine transaction type (DEBIT or CREDIT)
        tx_type = "DEBIT" if tx.sender_wallet_id == wallet.id else "CREDIT"
        
        result.append({
            "id": tx.id,
            "amount": float(tx.amount),
            "type": tx_type,
            "status": tx.status,
            "created_at": tx.created_at
        })
    
    # Generate next cursor if there's more
    next_cursor = None
    if has_next and transactions:
        last_tx = transactions[-1]
        next_cursor = encode_cursor(last_tx.created_at, last_tx.id)
    
    return {
        "data": result,
        "next_cursor": next_cursor
    }

