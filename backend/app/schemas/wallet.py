from pydantic import BaseModel, field_validator

class WalletResponse(BaseModel):
    wallet_id: int
    name: str
    balance: float
    
    class Config:
        from_attributes = True

class UpdateWalletNameRequest(BaseModel):
    name: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Wallet name must be at least 2 characters')
        if len(v) > 100:
            raise ValueError('Wallet name cannot exceed 100 characters')
        return v
