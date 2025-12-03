from pydantic import BaseModel, EmailStr
from typing import Optional


# -------------------------------
# STUDENT SCHEMAS
# -------------------------------
class StudentBase(BaseModel):
    name: str
    parent_name: str
    register_no: str
    student_class: str


class StudentCreate(StudentBase):
    password: str


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    parent_name: Optional[str] = None
    register_no: Optional[str] = None
    student_class: Optional[str] = None
    password: Optional[str] = None


class ParentBase(BaseModel):
    parent_name: str
    phone_number: str
    email: EmailStr


class ParentCreate(ParentBase):
    password: str


class ParentUpdate(BaseModel):
    parent_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

# -------------------------------
# TOKEN SCHEMA
# -------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str
class SummaryBase(BaseModel):
    student_register_no: str
    image_name: str
    description: Optional[str] = None


class SummaryCreate(SummaryBase):
    image_data: bytes  # actual image bytes stored in DB


class SummaryResponse(SummaryBase):
    id: int

    class Config:
        orm_mode = True