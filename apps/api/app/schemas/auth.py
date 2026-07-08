"""
Pydantic schemas for the auth endpoints.

These define exactly what shape of JSON the API accepts and returns --
separate from our SQLAlchemy models (which represent DB tables). Never
return a raw SQLAlchemy model directly from an endpoint: it might leak
internal fields (like hashed_password) that clients should never see.
"""

import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    tenant_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    tenant_id: uuid.UUID
    role: str

    model_config = {"from_attributes": True}  # allows building this from an ORM object


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
