import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.tasks.models import DisputeStatus, RemittanceStatus, TimeSegmentStatus


# Task Schemas
class TaskBase(BaseModel):
    title: str
    description: str | None = None
    rate_amount: Decimal = Field(default=0)
    currency: str = Field(default="USD")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("title cannot be empty")
        if len(value) > 255:
            raise ValueError("title too long")
        return value.strip()

    @field_validator("rate_amount")
    @classmethod
    def validate_rate(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("rate_amount must be positive")
        return value


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    rate_amount: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)


class TaskPublic(TaskBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TasksPublic(BaseModel):
    data: list[TaskPublic]
    count: int


# WorkLog Schemas
class WorkLogBase(BaseModel):
    amount: Decimal = Field(default=0)
    remittance_status: RemittanceStatus = Field(default=RemittanceStatus.UNREMITTED)


class WorkLogCreate(BaseModel):
    task_id: uuid.UUID
    worker_id: uuid.UUID


class WorkLogPublic(WorkLogBase):
    id: uuid.UUID
    worker_id: uuid.UUID
    task_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class WorkLogsPublic(BaseModel):
    data: list[WorkLogPublic]
    count: int


# TimeSegment Schemas
class TimeSegmentBase(BaseModel):
    start_time: datetime
    end_time: datetime
    duration_hours: Decimal
    status: TimeSegmentStatus = Field(default=TimeSegmentStatus.PENDING)


class TimeSegmentCreate(TimeSegmentBase):
    work_log_id: uuid.UUID


class TimeSegmentUpdate(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_hours: Decimal | None = None
    status: TimeSegmentStatus | None = None


class TimeSegmentPublic(TimeSegmentBase):
    id: uuid.UUID
    work_log_id: uuid.UUID
    remittance_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# Dispute Schemas
class DisputeCreate(BaseModel):
    reason: str


class DisputePublic(BaseModel):
    id: uuid.UUID
    time_segment_id: uuid.UUID
    reason: str
    status: DisputeStatus
    resolution_notes: str | None
    created_at: datetime
    resolved_at: datetime | None
