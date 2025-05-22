# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    google_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)