from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TransferRequest(BaseModel):
    """Request to transfer money between wallets"""
    receiver_user_id: int
    source_currency: str = Field(..., pattern="^(USD|INR|EUR|GBP|JPY|AUD)$")
    target_currency: str = Field(..., pattern="^(USD|INR|EUR|GBP|JPY|AUD)$")
    amount: float = Field(..., gt=0, description="Amount to transfer in source currency")

class TransferResponse(BaseModel):
    """Response after successful/failed transfer"""
    transaction_id: int
    status: str
    source_amount: float
    source_currency: str
    target_amount: float
    target_currency: str
    fx_rate: float

class TransactionItem(BaseModel):
    """Single transaction in history"""
    id: int
    source_amount: float
    source_currency: str
    target_amount: float
    target_currency: str
    fx_rate: float
    type: str  # DEBIT or CREDIT
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TransactionHistoryResponse(BaseModel):
    """Paginated transaction history"""
    data: list[TransactionItem]
    next_cursor: Optional[str] = None

