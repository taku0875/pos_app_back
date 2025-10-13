from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str

class UserDisplay(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    username: str # email
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None