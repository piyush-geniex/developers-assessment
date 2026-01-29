import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel

from app.models import User


# Enums
class TimeSegmentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DISPUTED = "DISPUTED"
    SETTLED = "SETTLED"
    REJECTED = "REJECTED"


class RemittanceStatus(str, Enum):
    REMITTED = "REMITTED"
    UNREMITTED = "UNREMITTED"


class DisputeStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


# Models
class Task(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    rate_amount: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    created_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    work_logs: list["WorkLog"] = Relationship(back_populates="task")


class WorkLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worker_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    task_id: uuid.UUID = Field(foreign_key="task.id", nullable=False)
    remittance_status: RemittanceStatus = Field(default=RemittanceStatus.UNREMITTED)
    amount: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    user: User = Relationship(back_populates="work_logs")
    task: Task = Relationship(back_populates="work_logs")
    time_segments: list["TimeSegment"] = Relationship(back_populates="work_log")


class TimeSegment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    work_log_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False)
    remittance_id: uuid.UUID | None = Field(default=None)

    start_time: datetime
    end_time: datetime
    duration_hours: Decimal = Field(default=0, max_digits=6, decimal_places=2)
    rate_at_recording: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    status: TimeSegmentStatus = Field(default=TimeSegmentStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    work_log: WorkLog = Relationship(back_populates="time_segments")
    disputes: list["Dispute"] = Relationship(back_populates="time_segment")


class Dispute(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    time_segment_id: uuid.UUID = Field(foreign_key="timesegment.id", nullable=False)
    reason: str
    status: DisputeStatus = Field(default=DisputeStatus.OPEN)
    resolution_notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None

    time_segment: TimeSegment = Relationship(back_populates="disputes")