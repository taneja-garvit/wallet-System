from sqlalchemy.orm import Session
from app.repositories.user_repo import get_user_by_email, create_user
from app.core.security import hash_password, verify_password, create_access_token

def signup(db: Session, name: str, email: str, password: str):
    """
    Create user account.
    
    Note: Wallets are NOT automatically created.
    Users must explicitly create wallets for desired currencies via POST /wallets.
    
    This design allows:
    - Users to choose which currencies they need
    - Clean separation of user identity and financial accounts
    - Flexibility in wallet management
    """
    if get_user_by_email(db, email):
        raise ValueError("User already exists")

    try:
        user = create_user(db, name, email, hash_password(password))
        db.commit()
    except Exception:
        db.rollback()
        raise

def login(db: Session, email: str, password: str):
    """Authenticate user and return JWT token"""
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    return create_access_token(user.id)
