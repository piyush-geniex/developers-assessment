from datetime import datetime
from pydantic import BaseModel, field_validator


class FreelancerCreate(BaseModel):
    name: str
    email: str
    rate_per_hour: float

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value is None:
            raise ValueError("name is required")
        if not isinstance(value, str):
            raise ValueError("name must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("name cannot be empty")
        if len(value) > 255:
            raise ValueError("name too long")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if value is None:
            raise ValueError("email is required")
        if not isinstance(value, str):
            raise ValueError("email must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("email cannot be empty")
        if "@" not in value:
            raise ValueError("invalid email format")
        return value

    @field_validator("rate_per_hour")
    @classmethod
    def validate_rate(cls, value: float) -> float:
        if value is None:
            raise ValueError("rate_per_hour is required")
        if not isinstance(value, (int, float)):
            raise ValueError("rate_per_hour must be a number")
        if value < 0:
            raise ValueError("rate_per_hour cannot be negative")
        return float(value)


class WorkLogCreate(BaseModel):
    freelancer_id: int
    task_name: str

    @field_validator("freelancer_id")
    @classmethod
    def validate_freelancer_id(cls, value: int) -> int:
        if value is None:
            raise ValueError("freelancer_id is required")
        if not isinstance(value, int):
            raise ValueError("freelancer_id must be an integer")
        if value <= 0:
            raise ValueError("freelancer_id must be positive")
        return value

    @field_validator("task_name")
    @classmethod
    def validate_task_name(cls, value: str) -> str:
        if value is None:
            raise ValueError("task_name is required")
        if not isinstance(value, str):
            raise ValueError("task_name must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("task_name cannot be empty")
        if len(value) > 255:
            raise ValueError("task_name too long")
        return value


class TimeEntryCreate(BaseModel):
    worklog_id: int
    description: str
    hours: float
    rate: float

    @field_validator("worklog_id")
    @classmethod
    def validate_worklog_id(cls, value: int) -> int:
        if value is None:
            raise ValueError("worklog_id is required")
        if not isinstance(value, int):
            raise ValueError("worklog_id must be an integer")
        if value <= 0:
            raise ValueError("worklog_id must be positive")
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        if value is None:
            raise ValueError("description is required")
        if not isinstance(value, str):
            raise ValueError("description must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("description cannot be empty")
        if len(value) > 500:
            raise ValueError("description too long")
        return value

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, value: float) -> float:
        if value is None:
            raise ValueError("hours is required")
        if not isinstance(value, (int, float)):
            raise ValueError("hours must be a number")
        if value <= 0:
            raise ValueError("hours must be positive")
        if value > 24:
            raise ValueError("hours cannot exceed 24")
        return float(value)

    @field_validator("rate")
    @classmethod
    def validate_rate(cls, value: float) -> float:
        if value is None:
            raise ValueError("rate is required")
        if not isinstance(value, (int, float)):
            raise ValueError("rate must be a number")
        if value < 0:
            raise ValueError("rate cannot be negative")
        return float(value)


class PaymentCreate(BaseModel):
    worklog_ids: list[int]
    start_date: str
    end_date: str

    @field_validator("worklog_ids")
    @classmethod
    def validate_worklog_ids(cls, value: list) -> list:
        if value is None:
            raise ValueError("worklog_ids is required")
        if not isinstance(value, list):
            raise ValueError("worklog_ids must be a list")
        if len(value) == 0:
            raise ValueError("worklog_ids cannot be empty")
        for wl_id in value:
            if not isinstance(wl_id, int):
                raise ValueError("all worklog_ids must be integers")
            if wl_id <= 0:
                raise ValueError("all worklog_ids must be positive")
        return value

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, value: str) -> str:
        if value is None:
            raise ValueError("start_date is required")
        if not isinstance(value, str):
            raise ValueError("start_date must be a string")
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            raise ValueError("invalid start_date format")
        return value

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, value: str) -> str:
        if value is None:
            raise ValueError("end_date is required")
        if not isinstance(value, str):
            raise ValueError("end_date must be a string")
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            raise ValueError("invalid end_date format")
        return value


class FreelancerResponse(BaseModel):
    id: int
    name: str
    email: str
    rate_per_hour: float
    created_at: datetime


class WorkLogResponse(BaseModel):
    id: int
    freelancer_id: int
    task_name: str
    status: str
    total_amount: float
    created_at: datetime
    updated_at: datetime


class TimeEntryResponse(BaseModel):
    id: int
    worklog_id: int
    description: str
    hours: float
    rate: float
    amount: float
    entry_date: datetime
    created_at: datetime


class PaymentResponse(BaseModel):
    id: int
    freelancer_id: int
    total_amount: float
    payment_date: datetime
    status: str
    worklog_ids: str
    created_at: datetime
