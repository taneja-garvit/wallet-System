from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.auth import SignupRequest, LoginRequest
from app.services.auth_service import signup, login
from app.api.deps import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup_api(req: SignupRequest, db: Session = Depends(get_db)):
    try:
        signup(db, req.name, req.email, req.password)
        return {"message": "User created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/login")
def login_api(req:LoginRequest, db:Session=Depends(get_db)):
    try:
        token = login(db, req.email, req.password)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))