import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TimeSegment(SQLModel, table=True):
    """Individual time recording for a worklog"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False, ondelete="CASCADE", index=True)
    hours: float = Field(ge=0)
    rate: float = Field(ge=0)
    recorded_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    is_removed: bool = Field(default=False)


class Adjustment(SQLModel, table=True):
    """Retroactive adjustments (deductions or additions) to worklogs"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False, ondelete="CASCADE", index=True)
    amount: float = Field()  # Can be negative for deductions
    reason: str = Field(max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Remittance(SQLModel, table=True):
    """Payment attempt for a user in a given period"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True)
    amount: float = Field(ge=0)
    period_start: datetime = Field(index=True)
    period_end: datetime = Field(index=True)
    status: str = Field(max_length=50, index=True)  # PENDING, COMPLETED, FAILED, CANCELLED
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    completed_at: Optional[datetime] = Field(default=None)


class WorkLogSettlement(SQLModel, table=True):
    """Tracks which worklogs were included in which remittances"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False, ondelete="CASCADE", index=True)
    remittance_id: uuid.UUID = Field(foreign_key="remittance.id", nullable=False, ondelete="CASCADE", index=True)
    amount_settled: float = Field()  # Amount from this worklog included in remittance
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class WorkLog(SQLModel, table=True):
    """Container for all work done against a task"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True)
    task_name: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
