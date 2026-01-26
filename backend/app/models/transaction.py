from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DateTime, Index
from datetime import datetime
from app.models.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)

    sender_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    receiver_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False)  # PENDING / SUCCESS / FAILED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes for efficient transaction history queries
    __table_args__ = (
        Index('idx_sender_created', 'sender_wallet_id', 'created_at', 'id'),
        Index('idx_receiver_created', 'receiver_wallet_id', 'created_at', 'id'),
    )
