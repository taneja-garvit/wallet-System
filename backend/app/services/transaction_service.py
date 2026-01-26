from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from typing import Optional
from decimal import Decimal

from app.repositories.wallet_repo import (
    get_wallet_by_user_and_currency,
    get_all_wallets_by_user,
    lock_wallets_ordered
)
from app.repositories.transaction_repo import (
    get_transaction_by_idempotency_key,
    create_transaction,
    get_user_transactions
)
from app.services.fx_service import get_fx_service
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
    source_currency: str,
    target_currency: str,
    amount: float,
    idempotency_key: str
) -> dict:
    """
    Transfer money between users with multi-currency support and FX conversion.
    
    Features:
    - Multi-currency support with FX conversion
    - Idempotent (same key = same result)
    - ACID guarantees
    - Deadlock prevention
    - Balance validation
    - FX audit trail
    
    Flow:
    1. Validate currencies and get FX rate
    2. Check idempotency (return existing if found)
    3. Validate inputs
    4. Lock wallets in deterministic order
    5. Check sender balance
    6. Apply FX conversion and balance updates
    7. Create immutable transaction record with FX metadata
    8. Commit atomically
    """
    
    # Step 1: Validate currencies and get FX rate
    fx_service = get_fx_service()
    
    if not fx_service.is_currency_supported(source_currency):
        raise ValueError(f"Source currency {source_currency} is not supported")
    
    if not fx_service.is_currency_supported(target_currency):
        raise ValueError(f"Target currency {target_currency} is not supported")
    
    # Get FX rate and converted amount
    amount_decimal = Decimal(str(amount))
    conversion_result = fx_service.convert(amount_decimal, source_currency, target_currency)
    
    if conversion_result is None:
        raise ValueError(f"Exchange rate not available for {source_currency} -> {target_currency}")
    
    target_amount, fx_rate = conversion_result
    fx_provider = fx_service.get_provider_name()
    fx_timestamp = fx_service.get_fx_timestamp()
    
    # Step 2: Idempotency check (BEFORE acquiring locks)
    existing_transaction = get_transaction_by_idempotency_key(db, idempotency_key)
    if existing_transaction:
        # Validate that payload matches existing transaction
        sender_wallet = get_wallet_by_user_and_currency(db, sender_user_id, source_currency)
        receiver_wallet = get_wallet_by_user_and_currency(db, receiver_user_id, target_currency)
        
        if not sender_wallet or not receiver_wallet:
            raise ValueError("Wallet not found")
        
        # Check if payload matches
        if (existing_transaction.sender_wallet_id != sender_wallet.id or
            existing_transaction.receiver_wallet_id != receiver_wallet.id or
            existing_transaction.source_amount != amount_decimal or
            existing_transaction.source_currency != source_currency or
            existing_transaction.target_currency != target_currency):
            # Same key but different payload - conflict!
            raise ValueError("IDEMPOTENCY_KEY_CONFLICT")
        
        # Return existing result - same idempotency key = same response
        return {
            "transaction_id": existing_transaction.id,
            "status": existing_transaction.status,
            "source_amount": float(existing_transaction.source_amount),
            "source_currency": existing_transaction.source_currency,
            "target_amount": float(existing_transaction.target_amount),
            "target_currency": existing_transaction.target_currency,
            "fx_rate": float(existing_transaction.fx_rate)
        }
    
    # Step 3: Validate inputs
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    if sender_user_id == receiver_user_id and source_currency == target_currency:
        raise ValueError("Cannot transfer to yourself in the same currency")
    
    # Step 4: Get wallets by currency
    sender_wallet = get_wallet_by_user_and_currency(db, sender_user_id, source_currency)
    receiver_wallet = get_wallet_by_user_and_currency(db, receiver_user_id, target_currency)
    
    if not sender_wallet:
        raise ValueError(f"Sender does not have a {source_currency} wallet")
    if not receiver_wallet:
        raise ValueError(f"Receiver does not have a {target_currency} wallet")
    
    sender_wallet_id = sender_wallet.id
    receiver_wallet_id = receiver_wallet.id
    
    # Step 5: Start DB transaction (everything below is atomic)
    try:
        # Step 6: Lock wallets in deterministic order (deadlock prevention)
        # Always lock smaller wallet_id first
        sender_wallet_locked, receiver_wallet_locked = lock_wallets_ordered(
            db, sender_wallet_id, receiver_wallet_id
        )
        
        # Verify currencies match (defense in depth)
        if sender_wallet_locked.currency != source_currency:
            raise ValueError(f"Sender wallet currency mismatch")
        if receiver_wallet_locked.currency != target_currency:
            raise ValueError(f"Receiver wallet currency mismatch")
        
        # Step 7: Balance check (fail early)
        if sender_wallet_locked.balance < amount_decimal:
            # Create FAILED transaction record (important for audit trail)
            transaction = create_transaction(
                db=db,
                idempotency_key=idempotency_key,
                sender_wallet_id=sender_wallet_id,
                receiver_wallet_id=receiver_wallet_id,
                source_currency=source_currency,
                target_currency=target_currency,
                source_amount=amount_decimal,
                target_amount=target_amount,
                fx_rate=fx_rate,
                fx_provider=fx_provider,
                fx_timestamp=fx_timestamp,
                status=STATUS_FAILED
            )
            db.commit()
            return {
                "transaction_id": transaction.id,
                "status": STATUS_FAILED,
                "source_amount": float(amount_decimal),
                "source_currency": source_currency,
                "target_amount": float(target_amount),
                "target_currency": target_currency,
                "fx_rate": float(fx_rate),
                "error": "INSUFFICIENT_BALANCE"
            }
        
        # Step 8: Apply balance changes with FX conversion
        # Debit sender in source currency
        sender_wallet_locked.balance -= amount_decimal
        
        # Credit receiver in target currency (converted amount)
        receiver_wallet_locked.balance += target_amount
        
        # Step 9: Create immutable transaction record with FX metadata
        transaction = create_transaction(
            db=db,
            idempotency_key=idempotency_key,
            sender_wallet_id=sender_wallet_id,
            receiver_wallet_id=receiver_wallet_id,
            source_currency=source_currency,
            target_currency=target_currency,
            source_amount=amount_decimal,
            target_amount=target_amount,
            fx_rate=fx_rate,
            fx_provider=fx_provider,
            fx_timestamp=fx_timestamp,
            status=STATUS_SUCCESS
        )
        
        # Step 10: Commit (atomic)
        db.commit()
        
        return {
            "transaction_id": transaction.id,
            "status": STATUS_SUCCESS,
            "source_amount": float(amount_decimal),
            "source_currency": source_currency,
            "target_amount": float(target_amount),
            "target_currency": target_currency,
            "fx_rate": float(fx_rate)
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
                "source_amount": float(existing.source_amount),
                "source_currency": existing.source_currency,
                "target_amount": float(existing.target_amount),
                "target_currency": existing.target_currency,
                "fx_rate": float(existing.fx_rate)
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
    
    Returns transactions where user is either sender or receiver across ALL currencies.
    Uses cursor-based pagination for stable, efficient pagination.
    """
    # Get all user's wallets (across all currencies)
    wallets = get_all_wallets_by_user(db, user_id)
    if not wallets:
        raise ValueError("No wallets found for user")
    
    wallet_ids = [w.id for w in wallets]
    
    # Create wallet_id -> currency map for determining DEBIT/CREDIT
    wallet_id_map = {w.id: w.currency for w in wallets}
    
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
        wallet_ids=wallet_ids,
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
        is_sender = tx.sender_wallet_id in wallet_id_map
        tx_type = "DEBIT" if is_sender else "CREDIT"
        
        result.append({
            "id": tx.id,
            "source_amount": float(tx.source_amount),
            "source_currency": tx.source_currency,
            "target_amount": float(tx.target_amount),
            "target_currency": tx.target_currency,
            "fx_rate": float(tx.fx_rate),
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

