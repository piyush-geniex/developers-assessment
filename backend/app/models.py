import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# WorkLog models
from datetime import datetime
from pydantic import BaseModel, field_validator


class TimeEntry(BaseModel):
    date: str
    hours: float
    description: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        if value is None:
            raise ValueError("date is required")
        if not isinstance(value, str):
            raise ValueError("date must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("date cannot be empty")
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


class WorkLogCreate(BaseModel):
    freelancer_id: int
    task_name: str
    time_entries: list[TimeEntry]
    hourly_rate: float

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

    @field_validator("time_entries")
    @classmethod
    def validate_time_entries(cls, value: list) -> list:
        if value is None:
            raise ValueError("time_entries is required")
        if not isinstance(value, list):
            raise ValueError("time_entries must be a list")
        if len(value) == 0:
            raise ValueError("time_entries cannot be empty")
        return value

    @field_validator("hourly_rate")
    @classmethod
    def validate_hourly_rate(cls, value: float) -> float:
        if value is None:
            raise ValueError("hourly_rate is required")
        if not isinstance(value, (int, float)):
            raise ValueError("hourly_rate must be a number")
        if value <= 0:
            raise ValueError("hourly_rate must be positive")
        return value


class WorkLogUpdate(BaseModel):
    task_name: str | None = None
    time_entries: list[TimeEntry] | None = None
    hourly_rate: float | None = None
    status: str | None = None

    @field_validator("task_name")
    @classmethod
    def validate_task_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not isinstance(value, str):
            raise ValueError("task_name must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("task_name cannot be empty")
        if len(value) > 255:
            raise ValueError("task_name too long")
        return value

    @field_validator("hourly_rate")
    @classmethod
    def validate_hourly_rate(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if not isinstance(value, (int, float)):
            raise ValueError("hourly_rate must be a number")
        if value <= 0:
            raise ValueError("hourly_rate must be positive")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not isinstance(value, str):
            raise ValueError("status must be a string")
        value = value.strip().upper()
        if value not in ["PENDING", "PAID", "EXCLUDED"]:
            raise ValueError("status must be PENDING, PAID, or EXCLUDED")
        return value


class WorkLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    freelancer_id: int = Field(index=True)
    task_name: str = Field(max_length=255)
    time_entries: str = Field()
    total_hours: float = Field(default=0.0)
    hourly_rate: float = Field(default=0.0)
    total_earned: float = Field(default=0.0)
    status: str = Field(default="PENDING", max_length=50, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class WorkLogPublic(BaseModel):
    id: int
    freelancer_id: int
    task_name: str
    time_entries: list[TimeEntry]
    total_hours: float
    hourly_rate: float
    total_earned: float
    status: str
    created_at: datetime
    updated_at: datetime


class WorkLogsPublic(BaseModel):
    data: list[WorkLogPublic]
    count: int


class PaymentBatchRequest(BaseModel):
    worklog_ids: list[int]

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


class PaymentBatchResponse(BaseModel):
    processed: int
    total: int
    total_amount: float


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
