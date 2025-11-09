from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


class AnalysisJobBase(BaseModel):
    status: Optional[str] = None
    progress_percentage: Optional[int] = 0
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalysisJobCreate(AnalysisJobBase):
    project_id: UUID


class AnalysisJobUpdate(BaseModel):
    status: Optional[str] = None
    progress_percentage: Optional[int] = None
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalysisJobRead(AnalysisJobBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime
