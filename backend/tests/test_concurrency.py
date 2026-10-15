import os
import sys
import uuid
import concurrent.futures
from decimal import Decimal

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.core.security import create_access_token


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient session"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def user_pair_deadlock():
    """
    Creates User A and User B with known balances for Test A & Test B.
    Using real PostgreSQL database (Neon / configured DB).
    """
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:8]
    user_a = User(name=f"UserA_{suffix}", email=f"usera_{suffix}@concurrency.test", password_hash="dummy_hash")
    user_b = User(name=f"UserB_{suffix}", email=f"userb_{suffix}@concurrency.test", password_hash="dummy_hash")
    db.add_all([user_a, user_b])
    db.flush()

    starting_balance = Decimal("1000.00")
    wallet_a = Wallet(user_id=user_a.id, name="Wallet A", balance=starting_balance)
    wallet_b = Wallet(user_id=user_b.id, name="Wallet B", balance=starting_balance)
    db.add_all([wallet_a, wallet_b])
    db.commit()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    data = {
        "user_a_id": user_a.id,
        "user_b_id": user_b.id,
        "token_a": token_a,
        "token_b": token_b,
        "starting_balance": starting_balance,
        "starting_sum": starting_balance * 2,
    }
    db.close()
    return data


def test_a_concurrent_reversed_transfers_no_deadlocks(client, user_pair_deadlock):
    """
    Test A: Fire concurrent reversed transfers (50 A->B and 50 B->A) from 30 worker threads.
    Assert:
    - Zero deadlock errors (OperationalError deadlock detected).
    - Zero HTTP 500 errors.
    - All requests succeed (HTTP 200).
    """
    u = user_pair_deadlock
    transfer_amount = 5.00
    total_transfers_per_direction = 50

    def send_a_to_b(idx):
        return client.post(
            "/transactions/transfer",
            json={"receiver_user_id": u["user_b_id"], "amount": transfer_amount},
            headers={"Authorization": f"Bearer {u['token_a']}", "Idempotency-Key": str(uuid.uuid4())}
        )

    def send_b_to_a(idx):
        return client.post(
            "/transactions/transfer",
            json={"receiver_user_id": u["user_a_id"], "amount": transfer_amount},
            headers={"Authorization": f"Bearer {u['token_b']}", "Idempotency-Key": str(uuid.uuid4())}
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = []
        for i in range(total_transfers_per_direction):
            futures.append(executor.submit(send_a_to_b, i))
            futures.append(executor.submit(send_b_to_a, i))

        responses = [f.result() for f in futures]

    assert len(responses) == total_transfers_per_direction * 2

    # Assert no 500 internal server errors and no deadlock messages
    errors_500 = [r for r in responses if r.status_code == 500]
    deadlock_errors = [
        r for r in responses 
        if "deadlock" in r.text.lower()
    ]

    assert len(errors_500) == 0, f"Encountered {len(errors_500)} HTTP 500 responses: {[r.text for r in errors_500]}"
    assert len(deadlock_errors) == 0, f"Encountered deadlock errors: {[r.text for r in deadlock_errors]}"

    # Verify all completed with 200 SUCCESS
    success_responses = [r for r in responses if r.status_code == 200 and r.json().get("status") == "SUCCESS"]
    assert len(success_responses) == total_transfers_per_direction * 2


def test_b_balance_conservation(user_pair_deadlock):
    """
    Test B: After Test A's concurrent transfers, verify conservation of money.
    Assert:
    - Sum of both wallet balances strictly equals the starting sum.
    - Neither wallet balance is negative.
    """
    u = user_pair_deadlock
    db = SessionLocal()
    try:
        wallet_a = db.query(Wallet).filter(Wallet.user_id == u["user_a_id"]).one()
        wallet_b = db.query(Wallet).filter(Wallet.user_id == u["user_b_id"]).one()

        assert wallet_a.balance >= Decimal("0.00"), f"Wallet A has negative balance: {wallet_a.balance}"
        assert wallet_b.balance >= Decimal("0.00"), f"Wallet B has negative balance: {wallet_b.balance}"

        final_sum = wallet_a.balance + wallet_b.balance
        assert final_sum == u["starting_sum"], (
            f"Money conservation violated! Starting sum: {u['starting_sum']}, Final sum: {final_sum}"
        )
    finally:
        db.close()


def test_c_idempotency_race_condition(client):
    """
    Test C: Send the SAME transfer request with the SAME idempotency key from ~10 threads at once.
    Assert:
    - Exactly one transaction row is created in the database.
    - Exactly one debit occurs on sender and credit on receiver.
    - Every response returns HTTP 200 with the exact same transaction_id.
    """
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:8]
    user_c = User(name=f"UserC_{suffix}", email=f"userc_{suffix}@concurrency.test", password_hash="dummy_hash")
    user_d = User(name=f"UserD_{suffix}", email=f"userd_{suffix}@concurrency.test", password_hash="dummy_hash")
    db.add_all([user_c, user_d])
    db.flush()

    initial_c_balance = Decimal("500.00")
    initial_d_balance = Decimal("500.00")
    wallet_c = Wallet(user_id=user_c.id, name="Wallet C", balance=initial_c_balance)
    wallet_d = Wallet(user_id=user_d.id, name="Wallet D", balance=initial_d_balance)
    db.add_all([wallet_c, wallet_d])
    db.commit()

    token_c = create_access_token(user_c.id)
    id_c, id_d = user_c.id, user_d.id
    fixed_idempotency_key = str(uuid.uuid4())
    transfer_amount = 30.00
    db.close()

    def send_idempotent_request(thread_idx):
        return client.post(
            "/transactions/transfer",
            json={"receiver_user_id": id_d, "amount": transfer_amount},
            headers={"Authorization": f"Bearer {token_c}", "Idempotency-Key": fixed_idempotency_key}
        )

    num_threads = 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(send_idempotent_request, i) for i in range(num_threads)]
        responses = [f.result() for f in futures]

    # 1. Assert all responses return HTTP 200
    status_codes = [r.status_code for r in responses]
    assert status_codes == [200] * num_threads, f"Unexpected status codes: {status_codes}"

    # 2. Assert every response returns the EXACT SAME transaction_id
    tx_ids = [r.json().get("transaction_id") for r in responses]
    unique_tx_ids = set(tx_ids)
    assert len(unique_tx_ids) == 1, f"Multiple transaction IDs returned for same idempotency key: {unique_tx_ids}"
    single_tx_id = tx_ids[0]

    # 3. Assert exactly one transaction row exists in database for this key
    db = SessionLocal()
    try:
        db_transactions = db.query(Transaction).filter(
            Transaction.idempotency_key == fixed_idempotency_key
        ).all()
        assert len(db_transactions) == 1, (
            f"Expected exactly 1 transaction row in DB, found {len(db_transactions)}"
        )
        assert db_transactions[0].id == single_tx_id
        assert db_transactions[0].status == "SUCCESS"

        # 4. Assert exactly one debit happened on User C and one credit on User D
        fresh_wallet_c = db.query(Wallet).filter(Wallet.user_id == id_c).one()
        fresh_wallet_d = db.query(Wallet).filter(Wallet.user_id == id_d).one()

        expected_c = initial_c_balance - Decimal(str(transfer_amount))
        expected_d = initial_d_balance + Decimal(str(transfer_amount))

        assert fresh_wallet_c.balance == expected_c, (
            f"Sender debited incorrectly! Expected {expected_c}, got {fresh_wallet_c.balance}"
        )
        assert fresh_wallet_d.balance == expected_d, (
            f"Receiver credited incorrectly! Expected {expected_d}, got {fresh_wallet_d.balance}"
        )
    finally:
        db.close()
