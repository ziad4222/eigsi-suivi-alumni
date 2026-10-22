from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import ProfileStatus


class ProfileCreate(BaseModel):
    email: EmailStr
    student_number: str = Field(min_length=2, max_length=30)
    graduation_year: int = Field(ge=1950, le=2100)
    program: str = Field(min_length=2, max_length=120)
    employment_status: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=1, max_length=120)
    country: str = Field(min_length=1, max_length=120)
    consent: bool


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_number: str
    graduation_year: int
    program: str
    employment_status: str
    city: str
    country: str
    status: ProfileStatus
    last_confirmed_at: datetime | None


class ReviewRequest(BaseModel):
    decision: Literal["APPROVED", "CORRECTION", "REJECTED"]
    comment: str = Field(default="", max_length=2000)


class DashboardRead(BaseModel):
    alumni_count: int
    validated_count: int
    pending_count: int
    fresh_count: int
    updated_at: datetime


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class ProfileWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    full_name: str = Field(min_length=2, max_length=160)
    student_number: str = Field(min_length=2, max_length=30)
    graduation_year: int = Field(ge=1950, le=2100)
    program: str = Field(min_length=2, max_length=120)
    employment_status: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=1, max_length=120)
    country: str = Field(min_length=1, max_length=120)
    company: str = Field(default="", max_length=160)
    sector: str = Field(default="", max_length=120)
    mentor: bool = False
    consent: bool


class ImportedProfile(ProfileWrite):
    email: EmailStr


class CampaignWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=160)
    message: str = Field(min_length=10, max_length=4000)
