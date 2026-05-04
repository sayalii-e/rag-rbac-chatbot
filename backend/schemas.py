from pydantic import BaseModel
from typing import Literal

class UserCreate(BaseModel):
    username: str
    password: str
    role: Literal["engineering", "finance", "general", "hr", "marketing"] = "general"

class UserLogin(BaseModel):
    username: str
    password: str