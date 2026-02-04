from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime, String, UniqueConstraint
from datetime import datetime
from app.models.base import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    name = Column(String(100), nullable=False, default="My Wallet")  # User-customizable wallet name
    balance = Column(Numeric(10, 2), default=10000.00, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # One wallet per user (single currency: INR)
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_wallet_user_id'),
    )
