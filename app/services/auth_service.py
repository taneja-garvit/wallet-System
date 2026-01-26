from sqlalchemy.orm import Session
from app.repositories.user_repo import get_user_by_email, create_user
from app.repositories.wallet_repo import create_wallet
from app.core.security import hash_password, verify_password, create_access_token

def signup(db: Session, name: str, email: str, password: str):
    if get_user_by_email(db, email):
        raise Exception("User already exists")

    user = create_user(db, name, email, hash_password(password))
    create_wallet(db, user.id)

    db.commit()

def login(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise Exception("Invalid credentials")

    return create_access_token(user.id)
