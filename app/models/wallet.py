from sqlalchemy import Column, Integer, ForeignKey, Numeric
from app.models.base import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id=Column(integer, primary_key=True)
    user_id=Column(integer, ForeignKey("users.id"))
    balance=Column(numeric(10,2), default=0.00)
    created_at=Column(DateTime, default=datetime.utcnow)
    updated_at=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
