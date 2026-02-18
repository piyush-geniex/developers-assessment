import uuid
from datetime import datetime

from pydantic import Field, field_serializer, field_validator

from app.core.schemas import CustomModel, datetime_to_gmt_str


class TimeEntryOut(CustomModel):
    id: uuid.UUID
    description: str | None
    hours: float
    rate: float
    amount: float
    logged_at: datetime

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: object) -> uuid.UUID:
        if v is None:
            raise ValueError("id is required")
        if not isinstance(v, uuid.UUID):
            raise ValueError("id must be a UUID")
        return v

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: object) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("description must be a string")
        return v.strip() or None if isinstance(v, str) else v

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, v: object) -> float:
        if v is None:
            raise ValueError("hours is required")
        if not isinstance(v, (int, float)):
            raise ValueError("hours must be a number")
        return float(v)

    @field_validator("rate")
    @classmethod
    def validate_rate(cls, v: object) -> float:
        if v is None:
            raise ValueError("rate is required")
        if not isinstance(v, (int, float)):
            raise ValueError("rate must be a number")
        return float(v)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: object) -> float:
        if v is None:
            raise ValueError("amount is required")
        if not isinstance(v, (int, float)):
            raise ValueError("amount must be a number")
        return float(v)

    @field_validator("logged_at")
    @classmethod
    def validate_logged_at(cls, v: object) -> datetime:
        if v is None:
            raise ValueError("logged_at is required")
        if not isinstance(v, datetime):
            raise ValueError("logged_at must be a datetime")
        return v

    @field_serializer("logged_at")
    def _ser_logged_at(self, dt: datetime) -> str | None:
        return datetime_to_gmt_str(dt)


class WorklogListItem(CustomModel):
    id: uuid.UUID
    task_id: uuid.UUID
    task_name: str
    freelancer_id: uuid.UUID
    freelancer_name: str
    amount_earned: float
    status: str
    created_at: datetime

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: object) -> uuid.UUID:
        if v is None:
            raise ValueError("id is required")
        if not isinstance(v, uuid.UUID):
            raise ValueError("id must be a UUID")
        return v

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: object) -> uuid.UUID:
        if v is None:
            raise ValueError("task_id is required")
        if not isinstance(v, uuid.UUID):
            raise ValueError("task_id must be a UUID")
        return v

    @field_validator("task_name")
    @classmethod
    def validate_task_name(cls, v: str) -> str:
        if v is None:
            raise ValueError("task_name is required")
        if not isinstance(v, str):
            raise ValueError("task_name must be a string")
        return v.strip()

    @field_validator("freelancer_id")
    @classmethod
    def validate_freelancer_id(cls, v: object) -> uuid.UUID:
        if v is None:
            raise ValueError("freelancer_id is required")
        if not isinstance(v, uuid.UUID):
            raise ValueError("freelancer_id must be a UUID")
        return v

    @field_validator("freelancer_name")
    @classmethod
    def validate_freelancer_name(cls, v: str) -> str:
        if v is None:
            raise ValueError("freelancer_name is required")
        if not isinstance(v, str):
            raise ValueError("freelancer_name must be a string")
        return v.strip()

    @field_validator("amount_earned")
    @classmethod
    def validate_amount_earned(cls, v: object) -> float:
        if v is None:
            raise ValueError("amount_earned is required")
        if not isinstance(v, (int, float)):
            raise ValueError("amount_earned must be a number")
        return float(v)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v is None:
            raise ValueError("status is required")
        if not isinstance(v, str):
            raise ValueError("status must be a string")
        return v.strip()

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, v: object) -> datetime:
        if v is None:
            raise ValueError("created_at is required")
        if not isinstance(v, datetime):
            raise ValueError("created_at must be a datetime")
        return v

    @field_serializer("created_at")
    def _ser_created_at(self, dt: datetime) -> str | None:
        return datetime_to_gmt_str(dt)


class WorklogListResponse(CustomModel):
    data: list[WorklogListItem]
    count: int

    @field_validator("data")
    @classmethod
    def validate_data(cls, v: object) -> list[WorklogListItem]:
        if v is None:
            raise ValueError("data is required")
        if not isinstance(v, list):
            raise ValueError("data must be a list")
        return v

    @field_validator("count")
    @classmethod
    def validate_count(cls, v: object) -> int:
        if v is None:
            raise ValueError("count is required")
        if not isinstance(v, int):
            raise ValueError("count must be an integer")
        if v < 0:
            raise ValueError("count cannot be negative")
        return v


class WorklogDetailResponse(CustomModel):
    id: uuid.UUID
    task_id: uuid.UUID
    task_name: str
    freelancer_id: uuid.UUID
    freelancer_name: str
    amount_earned: float
    status: str
    created_at: datetime
    time_entries: list[TimeEntryOut]

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: object) -> uuid.UUID:
        if v is None:
            raise ValueError("id is required")
        if not isinstance(v, uuid.UUID):
            raise ValueError("id must be a UUID")
        return v

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: object) -> uuid.UUID:
        if v is None:
            raise ValueError("task_id is required")
        if not isinstance(v, uuid.UUID):
            raise ValueError("task_id must be a UUID")
        return v

    @field_validator("task_name")
    @classmethod
    def validate_task_name(cls, v: str) -> str:
        if v is None:
            raise ValueError("task_name is required")
        if not isinstance(v, str):
            raise ValueError("task_name must be a string")
        return v.strip()

    @field_validator("freelancer_id")
    @classmethod
    def validate_freelancer_id(cls, v: object) -> uuid.UUID:
        if v is None:
            raise ValueError("freelancer_id is required")
        if not isinstance(v, uuid.UUID):
            raise ValueError("freelancer_id must be a UUID")
        return v

    @field_validator("freelancer_name")
    @classmethod
    def validate_freelancer_name(cls, v: str) -> str:
        if v is None:
            raise ValueError("freelancer_name is required")
        if not isinstance(v, str):
            raise ValueError("freelancer_name must be a string")
        return v.strip()

    @field_validator("amount_earned")
    @classmethod
    def validate_amount_earned(cls, v: object) -> float:
        if v is None:
            raise ValueError("amount_earned is required")
        if not isinstance(v, (int, float)):
            raise ValueError("amount_earned must be a number")
        return float(v)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v is None:
            raise ValueError("status is required")
        if not isinstance(v, str):
            raise ValueError("status must be a string")
        return v.strip()

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, v: object) -> datetime:
        if v is None:
            raise ValueError("created_at is required")
        if not isinstance(v, datetime):
            raise ValueError("created_at must be a datetime")
        return v

    @field_validator("time_entries")
    @classmethod
    def validate_time_entries(cls, v: object) -> list[TimeEntryOut]:
        if v is None:
            raise ValueError("time_entries is required")
        if not isinstance(v, list):
            raise ValueError("time_entries must be a list")
        return v

    @field_serializer("created_at")
    def _ser_created_at(self, dt: datetime) -> str | None:
        return datetime_to_gmt_str(dt)


class PaymentBatchCreate(CustomModel):
    worklog_ids: list[uuid.UUID] | None = Field(default=None)
    exclude_worklog_ids: list[uuid.UUID] | None = Field(default=None)
    exclude_freelancer_ids: list[uuid.UUID] | None = Field(default=None)

    @field_validator("worklog_ids", mode="before")
    @classmethod
    def validate_worklog_ids(cls, v: object) -> list[uuid.UUID] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("worklog_ids must be a list")
        out: list[uuid.UUID] = []
        for i, x in enumerate(v):
            if isinstance(x, uuid.UUID):
                out.append(x)
            elif isinstance(x, str):
                try:
                    out.append(uuid.UUID(x))
                except ValueError:
                    raise ValueError(f"worklog_ids[{i}] is not a valid UUID")
            else:
                raise ValueError(f"worklog_ids[{i}] must be a UUID or string")
        return out

    @field_validator("exclude_worklog_ids", mode="before")
    @classmethod
    def validate_exclude_worklog_ids(cls, v: object) -> list[uuid.UUID] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("exclude_worklog_ids must be a list")
        out: list[uuid.UUID] = []
        for i, x in enumerate(v):
            if isinstance(x, uuid.UUID):
                out.append(x)
            elif isinstance(x, str):
                try:
                    out.append(uuid.UUID(x))
                except ValueError:
                    raise ValueError(f"exclude_worklog_ids[{i}] is not a valid UUID")
            else:
                raise ValueError(f"exclude_worklog_ids[{i}] must be a UUID or string")
        return out

    @field_validator("exclude_freelancer_ids", mode="before")
    @classmethod
    def validate_exclude_freelancer_ids(cls, v: object) -> list[uuid.UUID] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("exclude_freelancer_ids must be a list")
        out: list[uuid.UUID] = []
        for i, x in enumerate(v):
            if isinstance(x, uuid.UUID):
                out.append(x)
            elif isinstance(x, str):
                try:
                    out.append(uuid.UUID(x))
                except ValueError:
                    raise ValueError(f"exclude_freelancer_ids[{i}] is not a valid UUID")
            else:
                raise ValueError(f"exclude_freelancer_ids[{i}] must be a UUID or string")
        return out


class PaymentBatchResponse(CustomModel):
    id: uuid.UUID
    worklog_count: int = 0
    total_amount: float = 0.0

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: object) -> uuid.UUID:
        if v is None:
            raise ValueError("id is required")
        if not isinstance(v, uuid.UUID):
            raise ValueError("id must be a UUID")
        return v

    @field_validator("worklog_count")
    @classmethod
    def validate_worklog_count(cls, v: object) -> int:
        if v is None:
            return 0
        if not isinstance(v, int):
            raise ValueError("worklog_count must be an integer")
        if v < 0:
            raise ValueError("worklog_count cannot be negative")
        return v

    @field_validator("total_amount")
    @classmethod
    def validate_total_amount(cls, v: object) -> float:
        if v is None:
            return 0.0
        if not isinstance(v, (int, float)):
            raise ValueError("total_amount must be a number")
        return float(v)
