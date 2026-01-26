from pydantic import BaseModel, EmailStr, field_validator

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot exceed 72 bytes (bcrypt limitation)')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str