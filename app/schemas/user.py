from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class UserVerify(BaseModel):
    email: EmailStr
    code: str = Field(min_length=8, max_length=8, pattern=r"^[A-Za-z0-9]+$")


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class UserCreateResponse(BaseModel):
    code: int
    success: bool
    message: str
    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
