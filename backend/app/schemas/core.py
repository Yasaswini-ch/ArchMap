from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl
from pydantic import ConfigDict


# User
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


# Project
class ProjectBase(BaseModel):
    name: str
    repo_url: Optional[HttpUrl] = None
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    repo_url: Optional[HttpUrl] = None
    description: Optional[str] = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


# Prediction
class PredictionBase(BaseModel):
    kind: str
    score: Optional[float] = None
    payload: Optional[dict] = None
    file_path: Optional[str] = None


class PredictionCreate(PredictionBase):
    project_id: UUID


class PredictionRead(PredictionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    created_at: datetime
