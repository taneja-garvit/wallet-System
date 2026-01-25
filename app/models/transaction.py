from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DateTime
from datetime import datetime
from app.models.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String, unique=True, index=True)

    sender_wallet_id = Column(Integer, ForeignKey("wallets.id"))
    receiver_wallet_id = Column(Integer, ForeignKey("wallets.id"))

    amount = Column(Numeric)
    status = Column(String)  # PENDING / SUCCESS / FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
