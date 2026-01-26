from pydantic import BaseModel, Field
from typing import List

class CreateWalletRequest(BaseModel):
    """Request to create a new wallet in a specific currency"""
    currency: str = Field(..., pattern="^(USD|INR|EUR|GBP|JPY|AUD)$", 
                         description="Currency code (USD, INR, EUR, GBP, JPY, AUD)")

class WalletResponse(BaseModel):
    """Single wallet response"""
    wallet_id: int
    currency: str
    balance: float
    
    class Config:
        from_attributes = True

class WalletListResponse(BaseModel):
    """Response containing all user wallets"""
    wallets: List[WalletResponse]

