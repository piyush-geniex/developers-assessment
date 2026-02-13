import uuid
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


class RemittanceStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Remittance(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    amount: float = Field()
    status: RemittanceStatus = Field(default=RemittanceStatus.PENDING, index=True)
    period_start: datetime = Field(index=True)
    period_end: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class WorkLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    task_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    time_segments: list["TimeSegment"] = Relationship(back_populates="worklog", cascade_delete=True)
    adjustments: list["Adjustment"] = Relationship(back_populates="worklog", cascade_delete=True)


class TimeSegment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", index=True)
    hours: float = Field()
    rate: float = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    worklog: WorkLog | None = Relationship(back_populates="time_segments")


class Adjustment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", index=True)
    amount: float = Field()
    reason: str = Field(max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    worklog: WorkLog | None = Relationship(back_populates="adjustments")

