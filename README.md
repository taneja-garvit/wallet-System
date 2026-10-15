# Digital Wallet System (INR)

A full-stack, transactional digital wallet platform built with **FastAPI, PostgreSQL, and React**. Designed to maintain strict financial consistency, prevent double-spending, reduce deadlocks under concurrent load, and ensure end-to-end idempotency for money transfers.

## Architecture Overview

```text
                      +----------------------+
                      |     React 19 SPA     |
                      +----------+-----------+
                                 |
                       HTTP / JWT / Idempotency-Key
                                 |
                      +----------v-----------+
                      |   FastAPI Backend    |
                      |  Thread Limiter: 200 |
                      +----------+-----------+
                                 |
                 +---------------+----------------+
                 |                                |
       +---------v----------+          +----------v-----------+
       | Wallets            |          | Transactions         |
       | PostgreSQL         |          | PostgreSQL           |
       |                    |          |                      |
       | - One wallet/user  |          | - Idempotency keys   |
       | - NUMERIC(10, 2)   |          | - Audit records      |
       | - Row-level locks  |          | - Transaction history|
       +--------------------+          +----------------------+
```

## Core Design Decisions

### 1. Deterministic Lock Ordering

Wallet rows are locked in a consistent order based on `user_id` using PostgreSQL's `SELECT ... FOR UPDATE`.

- Both A → B and B → A transfers acquire locks in the same order.
- Consistent lock ordering prevents circular-wait deadlocks between competing transfers.
- Relevant implementation: [`wallet_repo.py`](backend/app/repositories/wallet_repo.py).

### 2. Combined Fetch and Lock

Wallet selection and row locking are performed in a single database query using SQLAlchemy's `with_for_update()`.

This reduces redundant database round trips and ensures the wallet rows are locked when selected.

### 3. End-to-End Idempotency

Every transfer requires an `Idempotency-Key` header.

- The frontend generates a UUID using `crypto.randomUUID()`.
- The same key is reused when retrying the same transaction after a timeout or uncertain response.
- The database enforces a unique constraint on `transactions.idempotency_key`.
- Concurrent duplicate requests are handled through database integrity checks, transaction rollback, and reconciliation with the existing transaction.

Relevant implementation: [`TransferModal.jsx`](frontend/src/components/TransferModal.jsx).

### 4. Monetary Precision

Financial amounts are stored using PostgreSQL `NUMERIC(10, 2)` and processed using Python's `Decimal`.

```python
Decimal(str(amount))
```

This avoids the precision errors associated with binary floating-point arithmetic in financial calculations.

### 5. Worker Pool Sizing

The Starlette/AnyIO worker thread limiter is configured to allow up to 200 worker threads.

This allows synchronous route handlers to process concurrent requests, although actual throughput remains dependent on database connection limits, lock contention, and available resources.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT |
| Concurrency Control | PostgreSQL row-level locking |
| Idempotency | UUID keys and database uniqueness constraints |
| Testing | Pytest |
| Load Testing | k6 |
| Database Hosting | Neon PostgreSQL |

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── repositories/
│   │   └── ...
│   ├── tests/
│   │   └── test_concurrency.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       └── components/
│           └── TransferModal.jsx
├── load_test.js
├── SINGLE_CURRENCY_MIGRATION.md
└── README.md
```

## Local Setup & Quickstart

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL database (local or hosted)

### 1. Backend Setup

```bash
cd backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# Apply database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Configure the required database connection and application environment variables before starting the backend.

### 2. Frontend Setup

Open a separate terminal:

```bash
cd frontend

npm install
npm run dev
```

Use the local URL printed by the frontend development server.

## Testing

### 1. Pytest Concurrency & Integrity Suite

The concurrency test suite in [`test_concurrency.py`](backend/tests/test_concurrency.py) uses PostgreSQL to test transfer integrity under concurrent execution.

**Test A — Deadlock Freedom**

Runs 100 concurrent transfers in opposite directions between two accounts using 30 worker threads.

**Test B — Balance Conservation**

Checks that the total balance remains unchanged and that no wallet balance becomes negative.

**Test C — Idempotency Race Condition**

Sends 10 concurrent requests using the same idempotency key and verifies that only one transaction is created and the requests resolve to the same transaction ID.

Run the tests:

```bash
cd backend

./venv/bin/pytest tests/test_concurrency.py -v -s
```

> These tests require a correctly configured PostgreSQL database and should be run against a dedicated test database.

### 2. k6 Load Testing

The load test in [`load_test.js`](load_test.js) simulates concurrent traffic with up to 150 virtual users.

Ensure the backend is running and the test configuration points to the correct API URL.

```bash
k6 run load_test.js
```

## Verified Benchmarks & Empirical Results

The following results were recorded during a test run against the application connected to a Neon PostgreSQL instance.

**Test configuration**

- Database connection pool size: 50
- Maximum overflow connections: 100
- Connection pool timeout: 30 seconds
- Maximum virtual users: 150

### Automated Concurrency Tests

```text
tests/test_concurrency.py::test_a_concurrent_reversed_transfers_no_deadlocks PASSED
tests/test_concurrency.py::test_b_balance_conservation PASSED
tests/test_concurrency.py::test_c_idempotency_race_condition PASSED

================= 3 passed in 195.53s =================
```

### k6 Load Test Results

| Metric | Result |
|---|---:|
| Total Requests | 1,068 |
| Transfer Requests | 1,018 |
| Completed Iterations | 1,013 |
| Peak Virtual Users | 150 |
| HTTP 500 Errors | 0 |
| HTTP 409 Conflicts | 0 |
| Observed Deadlock Exceptions | 0 |
| Observed Connection Pool Exhaustion Errors | 0 |
| Balance Conservation | ₹0.00 net change |
| Starting Total Balance | ₹78,009,503.00 |
| Ending Total Balance | ₹78,009,503.00 |
| HTTP 200 Transfer Success Rate | 95.04% |
| Requests Exceeding the 60-Second Client Timeout | 53 |
| Median Latency (p50) | 5.57 seconds |
| p95 Latency | 59.02 seconds |
| p99 Latency | 60.00 seconds |

*Results are specific to the recorded test environment and workload. They are not guarantees of production performance.*

## Performance Analysis: The Lock Contention Bottleneck

The load test demonstrated that preserving transaction integrity does not automatically guarantee low latency under heavy contention.

### 1. Contention Between Transfers

With 150 virtual users operating on a finite set of 50 accounts, concurrent transfers can compete for the same wallet rows.

Row-level locks ensure that conflicting operations are serialized, preserving correctness but increasing wait times.

### 2. Database Network Latency

The test database was hosted on Neon in AWS `us-east-1`, with an estimated application-to-database round-trip latency of approximately 150 ms during testing.

Multiple database interactions within each transaction can amplify this latency, particularly when requests must wait for locks held by other transactions.

### 3. Observed Impact

The recorded load test showed:

- No observed deadlocks.
- No observed HTTP 500 or HTTP 409 responses.
- No net change in the total wallet balance.
- 53 requests exceeding the configured 60-second client timeout.
- A p95 latency of 59.02 seconds.

The results highlight the trade-off between pessimistic locking, financial correctness, and throughput under contention.

## Production Optimization Roadmap

### 1. Co-locate the Application and Database

Deploy the backend in the same cloud region as PostgreSQL, ideally within the same private network where supported.

This can reduce network latency between the application and database.

### 2. Reduce Transaction Duration

- Minimize database round trips within transaction boundaries.
- Keep external API calls outside database transactions.
- Profile lock wait times and query execution plans.
- Tune database connection pools according to measured workload and database limits.

### 3. Evaluate a Ledger-Based Architecture

Consider an append-only, double-entry ledger for recording financial movements, with balances maintained as transactionally consistent projections or account totals.

This improves auditability and makes financial reconciliation easier. However, a ledger alone does not eliminate contention: concurrent updates to the same account still require appropriate serialization or concurrency control.

### 4. Expand Load Testing

- Test with larger and more diverse account populations.
- Separate hot-account contention tests from distributed-account workloads.
- Measure throughput, lock wait duration, database utilization, and latency percentiles.
- Test retries, duplicate requests, transaction failures, and recovery scenarios.

## Key Engineering Takeaways

- **Consistency:** Use database transactions and row-level locks to protect concurrent balance updates.
- **Deadlock prevention:** Acquire multiple locks in a deterministic order.
- **Idempotency:** Combine client-side retry behavior with database-enforced uniqueness.
- **Financial precision:** Use decimal arithmetic and fixed-precision database types.
- **Testing:** Validate concurrency and balance conservation against PostgreSQL.
- **Performance:** Measure real database contention rather than assuming that correctness implies scalability.

---

*Built to explore transactional correctness, concurrent financial operations, database locking, idempotent API design, and performance engineering in a full-stack application.*
