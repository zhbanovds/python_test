from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"
    chat_id: int  # добавляем chat_id

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    chat_id: Optional[str] 

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginHistoryOut(BaseModel):
    login_time: datetime
    ip_address: str
    login_method: str

    class Config:
        orm_mode = True
