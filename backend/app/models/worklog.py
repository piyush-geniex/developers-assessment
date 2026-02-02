"""
Worklog model
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class Worklog(SQLModel, table=True):
    """Worklog containing time entries for a task by a freelancer"""
    
    __tablename__ = "worklogs"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    freelancer_id: uuid.UUID = Field(foreign_key="freelancers.id", nullable=False)
    task_id: uuid.UUID = Field(foreign_key="tasks.id", nullable=False)
    description: Optional[str] = Field(default=None)
    total_hours: Decimal = Field(default=Decimal("0"), decimal_places=2)
    total_amount: Decimal = Field(default=Decimal("0"), decimal_places=2)
    status: str = Field(default="pending", max_length=50)  # pending, paid, cancelled
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
