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
    worklogs: list["WorkLog"] = Relationship(back_populates="freelancer", cascade_delete=True)


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


# WorkLog and TimeEntry Models
from datetime import date, datetime
from enum import Enum


class WorkLogStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"


class WorkLogBase(SQLModel):
    task_name: str = Field(min_length=1, max_length=255)
    status: WorkLogStatus = Field(default=WorkLogStatus.PENDING)


class WorkLog(WorkLogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    freelancer_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )

    freelancer: User = Relationship(back_populates="worklogs")
    time_entries: list["TimeEntry"] = Relationship(
        back_populates="worklog", cascade_delete=True
    )


class TimeEntryBase(SQLModel):
    date: date
    hours: float = Field(gt=0)
    hourly_rate: float = Field(gt=0)
    description: str | None = Field(default=None, max_length=255)


class TimeEntry(TimeEntryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(
        foreign_key="worklog.id", nullable=False, ondelete="CASCADE"
    )
    is_paid: bool = Field(default=False, index=True)
    paid_at: datetime | None = Field(default=None, index=True)

    worklog: WorkLog = Relationship(back_populates="time_entries")


# Public Schemas
class WorkLogPublic(WorkLogBase):
    id: uuid.UUID
    # Actual user UUID for batch exclusion logic
    freelancer_uuid: uuid.UUID
    # Display-friendly freelancer identifier (kept for UI)
    freelancer_id: str
    freelancer_name: str
    total_earned: float = 0.0


class WorkLogsPublic(SQLModel):
    data: list[WorkLogPublic]
    count: int


class TimeEntryPublic(TimeEntryBase):
    id: uuid.UUID
    worklog_id: uuid.UUID
    is_paid: bool
    paid_at: datetime | None


class WorkLogDetail(WorkLogPublic):
    time_entries: list[TimeEntryPublic]


class PaymentBatchCreate(SQLModel):
    # Backwards-compatible: allow paying by worklog ids (pays all unpaid entries in those worklogs)
    worklog_ids: list[uuid.UUID] = []
    # Preferred for fine-grained payouts: pay specific time entries
    time_entry_ids: list[uuid.UUID] = []
    excluded_freelancer_ids: list[uuid.UUID] = []
