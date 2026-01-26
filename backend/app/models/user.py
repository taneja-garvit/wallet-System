from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id=Column(Integer, primary_key=True)
    name=Column(String, nullable=False)
    email = Column(String,nullable=False, unique=True,index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)