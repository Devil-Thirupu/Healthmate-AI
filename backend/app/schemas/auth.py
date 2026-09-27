from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: Optional[str] = "patient"
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    language_preference: Optional[str] = "en"

    @field_validator(
        "date_of_birth", "gender", "blood_group", "phone_number",
        "emergency_contact", "allergies", "chronic_conditions", "language_preference",
        mode="before"
    )
    @classmethod
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v.strip() if isinstance(v, str) else v

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_name(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    identifier: Optional[str] = None
    password: str

    @field_validator("email", "phone_number", "identifier", mode="before")
    @classmethod
    def clean_login_identifiers(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v.strip() if isinstance(v, str) else v

class MobileLogin(BaseModel):
    phone_number: str
    password: str

    @field_validator("phone_number", mode="before")
    @classmethod
    def clean_phone(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

class GoogleLoginRequest(BaseModel):
    id_token: str = Field(..., description="Google ID Token from Google Sign-In SDK")

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    language_preference: Optional[str] = None

    @field_validator(
        "full_name", "date_of_birth", "gender", "blood_group", "phone_number",
        "emergency_contact", "allergies", "chronic_conditions", "language_preference",
        mode="before"
    )
    @classmethod
    def clean_update_fields(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v.strip() if isinstance(v, str) else v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
