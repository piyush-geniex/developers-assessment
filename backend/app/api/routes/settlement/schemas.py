import re
import uuid

from pydantic import BaseModel, field_validator


class WorklogItem(BaseModel):
    """
    Response model for a single worklog entry.
    id: worklog id
    user_id: owner of the worklog
    title: task description
    amount: computed total (segments + adjustments)
    remittance_status: REMITTED or UNREMITTED
    """

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    amount: float
    remittance_status: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if value is None:
            raise ValueError("title is required")

        if not isinstance(value, str):
            raise ValueError("title must be a string")

        value = value.strip()

        if len(value) == 0:
            raise ValueError("title cannot be empty")

        if len(value) > 255:
            raise ValueError("title too long")

        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value is None:
            raise ValueError("amount is required")

        if not isinstance(value, int | float):
            raise ValueError("amount must be a number")

        return round(float(value), 2)

    @field_validator("remittance_status")
    @classmethod
    def validate_remittance_status(cls, value: str) -> str:
        if value is None:
            raise ValueError("remittance_status is required")

        if not isinstance(value, str):
            raise ValueError("remittance_status must be a string")

        value = value.strip().upper()

        if value not in ("REMITTED", "UNREMITTED"):
            raise ValueError("remittance_status must be REMITTED or UNREMITTED")

        return value


class WorklogListResponse(BaseModel):
    data: list[WorklogItem]
    count: int

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


class RemittanceItem(BaseModel):
    """
    Response model for a single remittance entry.
    id: remittance id
    user_id: worker who receives the payout
    amount: total payout amount
    status: PENDING, SETTLED, FAILED, CANCELLED
    period: settlement period e.g. 2026-02
    """

    id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    status: str
    period: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value is None:
            raise ValueError("amount is required")

        if not isinstance(value, int | float):
            raise ValueError("amount must be a number")

        return round(float(value), 2)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value is None:
            raise ValueError("status is required")

        if not isinstance(value, str):
            raise ValueError("status must be a string")

        value = value.strip().upper()

        if value not in ("PENDING", "SETTLED", "FAILED", "CANCELLED"):
            raise ValueError("status must be PENDING, SETTLED, FAILED, or CANCELLED")

        return value

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        if value is None:
            raise ValueError("period is required")

        if not isinstance(value, str):
            raise ValueError("period must be a string")

        value = value.strip()

        if not re.match(r"^\d{4}-\d{2}$", value):
            raise ValueError("period must be in YYYY-MM format")

        return value


class RemittanceResponse(BaseModel):
    data: list[RemittanceItem]
    count: int

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
