import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator


class RemittanceStatusEnum(str, Enum):
    REMITTED = "REMITTED"
    UNREMITTED = "UNREMITTED"


class WorkLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    task_id: str
    amount: float
    created_at: datetime
    updated_at: datetime

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: uuid.UUID) -> uuid.UUID:
        if value is None:
            raise ValueError("id is required")
        if not isinstance(value, uuid.UUID):
            raise ValueError("id must be a UUID")
        return value

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: uuid.UUID) -> uuid.UUID:
        if value is None:
            raise ValueError("user_id is required")
        if not isinstance(value, uuid.UUID):
            raise ValueError("user_id must be a UUID")
        return value

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, value: str) -> str:
        if value is None:
            raise ValueError("task_id is required")
        if not isinstance(value, str):
            raise ValueError("task_id must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("task_id cannot be empty")
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value is None:
            raise ValueError("amount is required")
        if not isinstance(value, (int, float)):
            raise ValueError("amount must be a number")
        return float(value)

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("created_at is required")
        if not isinstance(value, datetime):
            raise ValueError("created_at must be a datetime")
        return value

    @field_validator("updated_at")
    @classmethod
    def validate_updated_at(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("updated_at is required")
        if not isinstance(value, datetime):
            raise ValueError("updated_at must be a datetime")
        return value


class WorkLogsListResponse(BaseModel):
    data: list[WorkLogResponse]
    count: int

    @field_validator("data")
    @classmethod
    def validate_data(cls, value: list) -> list:
        if value is None:
            raise ValueError("data is required")
        if not isinstance(value, list):
            raise ValueError("data must be a list")
        return value

    @field_validator("count")
    @classmethod
    def validate_count(cls, value: int) -> int:
        if value is None:
            raise ValueError("count is required")
        if not isinstance(value, int):
            raise ValueError("count must be an integer")
        if value < 0:
            raise ValueError("count cannot be negative")
        return value


class RemittanceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    status: str
    period_start: datetime
    period_end: datetime
    created_at: datetime
    updated_at: datetime

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: uuid.UUID) -> uuid.UUID:
        if value is None:
            raise ValueError("id is required")
        if not isinstance(value, uuid.UUID):
            raise ValueError("id must be a UUID")
        return value

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: uuid.UUID) -> uuid.UUID:
        if value is None:
            raise ValueError("user_id is required")
        if not isinstance(value, uuid.UUID):
            raise ValueError("user_id must be a UUID")
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value is None:
            raise ValueError("amount is required")
        if not isinstance(value, (int, float)):
            raise ValueError("amount must be a number")
        return float(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value is None:
            raise ValueError("status is required")
        if not isinstance(value, str):
            raise ValueError("status must be a string")
        return value

    @field_validator("period_start")
    @classmethod
    def validate_period_start(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("period_start is required")
        if not isinstance(value, datetime):
            raise ValueError("period_start must be a datetime")
        return value

    @field_validator("period_end")
    @classmethod
    def validate_period_end(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("period_end is required")
        if not isinstance(value, datetime):
            raise ValueError("period_end must be a datetime")
        return value

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("created_at is required")
        if not isinstance(value, datetime):
            raise ValueError("created_at must be a datetime")
        return value

    @field_validator("updated_at")
    @classmethod
    def validate_updated_at(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("updated_at is required")
        if not isinstance(value, datetime):
            raise ValueError("updated_at must be a datetime")
        return value


class GenerateRemittancesResponse(BaseModel):
    remittances_created: int
    total_amount: float
    remittances: list[RemittanceResponse]

    @field_validator("remittances_created")
    @classmethod
    def validate_remittances_created(cls, value: int) -> int:
        if value is None:
            raise ValueError("remittances_created is required")
        if not isinstance(value, int):
            raise ValueError("remittances_created must be an integer")
        if value < 0:
            raise ValueError("remittances_created cannot be negative")
        return value

    @field_validator("total_amount")
    @classmethod
    def validate_total_amount(cls, value: float) -> float:
        if value is None:
            raise ValueError("total_amount is required")
        if not isinstance(value, (int, float)):
            raise ValueError("total_amount must be a number")
        return float(value)

    @field_validator("remittances")
    @classmethod
    def validate_remittances(cls, value: list) -> list:
        if value is None:
            raise ValueError("remittances is required")
        if not isinstance(value, list):
            raise ValueError("remittances must be a list")
        return value

