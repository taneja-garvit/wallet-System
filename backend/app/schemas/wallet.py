from pydantic import BaseModel

class WalletResponse(BaseModel):
    wallet_id: int
    balance: float
    
    class Config:
        from_attributes = True

