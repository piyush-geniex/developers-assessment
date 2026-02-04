import re
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class WorkLogWithEarnings(BaseModel):
    """
    wl: worklog
    fr: freelancer
    amt: amount
    hrs: hours
    """

    id: uuid.UUID
    item_id: uuid.UUID
    item_title: str
    hours: float
    payment_status: str
    freelancer_id: uuid.UUID
    freelancer_name: str
    created_at: datetime
    paid_at: datetime | None
    amount_earned: float


class WorkLogDetail(BaseModel):
    """
    wl: worklog
    segs: time segments
    """

    id: uuid.UUID
    item_id: uuid.UUID
    item_title: str
    hours: float
    payment_status: str
    freelancer_id: uuid.UUID
    freelancer_name: str
    hourly_rate: float
    created_at: datetime
    paid_at: datetime | None
    time_segments: list[dict]
    amount_earned: float


class PaymentBatchRequest(BaseModel):
    """Request to process payment batch"""

    worklog_ids: list[uuid.UUID]
    start_date: datetime | None = None
    end_date: datetime | None = None

    @field_validator("worklog_ids")
    @classmethod
    def validate_worklog_ids(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if value is None:
            raise ValueError("worklog_ids is required")

        if not isinstance(value, list):
            raise ValueError("worklog_ids must be a list")

        if len(value) == 0:
            raise ValueError("worklog_ids cannot be empty")

        return value


class FreelancerCreateRequest(BaseModel):
    """Request to create freelancer"""

    full_name: str
    hourly_rate: float
    status: str = "active"

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        if value is None:
            raise ValueError("full_name is required")

        if not isinstance(value, str):
            raise ValueError("full_name must be a string")

        value = value.strip()

        if len(value) == 0:
            raise ValueError("full_name cannot be empty")

        if len(value) > 255:
            raise ValueError("full_name too long")

        return value

    @field_validator("hourly_rate")
    @classmethod
    def validate_hourly_rate(cls, value: float) -> float:
        if value is None:
            raise ValueError("hourly_rate is required")

        if not isinstance(value, (int, float)):
            raise ValueError("hourly_rate must be a number")

        if value < 0:
            raise ValueError("hourly_rate cannot be negative")

        return float(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value is None:
            raise ValueError("status is required")

        if not isinstance(value, str):
            raise ValueError("status must be a string")

        value = value.strip().lower()

        if value not in ["active", "inactive"]:
            raise ValueError("status must be active or inactive")

        return value


class WorkLogCreateRequest(BaseModel):
    """Request to create worklog"""

    freelancer_id: uuid.UUID
    item_id: uuid.UUID
    item_title: str
    hours: float

    @field_validator("item_title")
    @classmethod
    def validate_item_title(cls, value: str) -> str:
        if value is None:
            raise ValueError("item_title is required")

        if not isinstance(value, str):
            raise ValueError("item_title must be a string")

        value = value.strip()

        if len(value) == 0:
            raise ValueError("item_title cannot be empty")

        if len(value) > 255:
            raise ValueError("item_title too long")

        return value

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, value: float) -> float:
        if value is None:
            raise ValueError("hours is required")

        if not isinstance(value, (int, float)):
            raise ValueError("hours must be a number")

        if value < 0:
            raise ValueError("hours cannot be negative")

        if value > 24:
            raise ValueError("hours cannot exceed 24")

        return float(value)


class TimeSegmentCreateRequest(BaseModel):
    """Request to create time segment"""

    worklog_id: uuid.UUID
    hours: float
    segment_date: datetime
    notes: str | None = None

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, value: float) -> float:
        if value is None:
            raise ValueError("hours is required")

        if not isinstance(value, (int, float)):
            raise ValueError("hours must be a number")

        if value < 0:
            raise ValueError("hours cannot be negative")

        if value > 24:
            raise ValueError("hours cannot exceed 24")

        return float(value)

    @field_validator("segment_date")
    @classmethod
    def validate_segment_date(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("segment_date is required")

        if not isinstance(value, datetime):
            raise ValueError("segment_date must be a datetime")

        return value
