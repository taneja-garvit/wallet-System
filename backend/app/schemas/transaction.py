from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransferRequest(BaseModel):
    receiver_user_id: int
    amount: float

class TransferResponse(BaseModel):
    transaction_id: int
    status: str
    amount: float

class TransactionItem(BaseModel):
    id: int
    amount: float
    type: str  # DEBIT or CREDIT
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TransactionHistoryResponse(BaseModel):
    data: list[TransactionItem]
    next_cursor: Optional[str] = None

