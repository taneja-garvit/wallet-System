from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime, String, UniqueConstraint, Index
from datetime import datetime
from app.models.base import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(String(3), nullable=False)  # USD, INR, EUR, etc.
    balance = Column(Numeric(10, 2), default=0.00, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # One wallet per currency per user
    __table_args__ = (
        UniqueConstraint('user_id', 'currency', name='uq_wallet_user_currency'),
        Index('idx_wallet_user_id', 'user_id'),  # Fast wallet lookup per user
    )
