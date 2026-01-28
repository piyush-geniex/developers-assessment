from enum import Enum
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class RemittanceStatus(str, Enum):
    remitted = 'remitted'
    unremitted = 'unremitted'


class TaskCreateIn(BaseModel):
    title: str
    description: Optional[str] = None


class TaskCreateOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    created_at: datetime


class WorkLogCreateIn(BaseModel):
    user_id: uuid.UUID
    task_id: uuid.UUID


class WorkLogCreateOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    task_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
