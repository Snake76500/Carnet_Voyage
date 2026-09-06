from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nom d'utilisateur unique")
    role: str = Field(default="guest", description="Rôle: 'admin' ou 'guest'")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Mot de passe en clair (sera haché)")

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
