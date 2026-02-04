from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

class TransferRequest(BaseModel):
    receiver_user_id: int
    amount: float
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > 1000000:  # Max 10 lakh INR per transaction
            raise ValueError('Amount cannot exceed ₹10,00,000')
        return round(v, 2)  # Round to 2 decimal places

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
