from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DateTime, Index
from datetime import datetime
from app.models.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)

    # Sender side
    sender_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    source_currency = Column(String(3), nullable=False)
    source_amount = Column(Numeric(10, 2), nullable=False)

    # Receiver side
    receiver_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    target_currency = Column(String(3), nullable=False)
    target_amount = Column(Numeric(10, 2), nullable=False)

    # FX metadata (for audit trail)
    fx_rate = Column(Numeric(20, 10), nullable=False)  # High precision for rates
    fx_provider = Column(String(50), nullable=False)  # e.g., "STATIC"
    fx_timestamp = Column(DateTime, nullable=False)

    # Status tracking
    status = Column(String(20), nullable=False)  # PENDING / SUCCESS / FAILED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes for efficient transaction history queries
    __table_args__ = (
        Index('idx_sender_created', 'sender_wallet_id', 'created_at', 'id'),
        Index('idx_receiver_created', 'receiver_wallet_id', 'created_at', 'id'),
        # Optional: FX analytics index
        Index('idx_fx_analytics', 'source_currency', 'target_currency', 'created_at'),
    )
