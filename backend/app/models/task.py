"""
Task model
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Task(SQLModel, table=True):
    """Task that freelancers log work against"""
    
    __tablename__ = "tasks"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    status: str = Field(default="active", max_length=50)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
