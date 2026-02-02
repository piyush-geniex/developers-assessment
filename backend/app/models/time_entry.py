"""
TimeEntry model
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class TimeEntry(SQLModel, table=True):
    """Individual time entry within a worklog"""
    
    __tablename__ = "time_entries"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklogs.id", nullable=False)
    start_time: datetime = Field(nullable=False)
    end_time: datetime = Field(nullable=False)
    hours: Decimal = Field(decimal_places=2, nullable=False)
    description: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
