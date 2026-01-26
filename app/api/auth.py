from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.auth import SignupRequest, LoginRequest
from app.services.auth_service import signup, login
from app.api.deps import get_db

router = APIRouter(prefix="/auth")

@router.post("/signup")
def signup_api(req:SignupRequest, db:Session=Depends(get_db)):
    try:
        signup(db, req.name, req.email, req.password)
        return {"message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login"):
    def login_api(req:LoginRequest, db:Session=Depends(get_db)):
        try:
            token = login(db, req.email, req.password)
            return {"access_token": token}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))