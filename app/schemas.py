# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_verified: bool

model_config = {
    "from_attributes": True
}


class TokenData(BaseModel):
    email: Optional[str] = None

class PasswordReset(BaseModel):
    token: str
    new_password: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str