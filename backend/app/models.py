import uuid
from datetime import date, datetime

from pydantic import EmailStr, field_validator
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
    worklogs: list["WorkLog"] = Relationship(back_populates="user")


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
    owner: "User" = Relationship(back_populates="items")
    worklogs: list["WorkLog"] = Relationship(back_populates="item")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Payment batch for grouping worklog payments
class PaymentBatch(SQLModel, table=True):
    __tablename__ = "payment_batch"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    total_amount: float = Field(default=0, ge=0)
    status: str = Field(default="completed", max_length=32, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


# WorkLog domain: freelancers log time against tasks (items)
class WorkLog(SQLModel, table=True):
    __tablename__ = "worklog"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    item_id: uuid.UUID = Field(foreign_key="item.id", nullable=False, index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    status: str = Field(default="pending", max_length=32, index=True)
    payment_batch_id: uuid.UUID | None = Field(
        default=None, foreign_key="payment_batch.id", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    item: "Item" = Relationship(back_populates="worklogs")
    user: "User" = Relationship(back_populates="worklogs")
    time_entries: list["TimeEntry"] = Relationship(
        back_populates="worklog", cascade_delete=True
    )


class TimeEntry(SQLModel, table=True):
    __tablename__ = "time_entry"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(
        foreign_key="worklog.id", nullable=False, ondelete="CASCADE", index=True
    )
    hours: float = Field(ge=0)
    rate: float = Field(ge=0)
    entry_date: date = Field(index=True)
    description: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    worklog: "WorkLog" = Relationship(back_populates="time_entries")


# API response schemas for worklog domain
class TimeEntryPublic(SQLModel):
    id: uuid.UUID
    worklog_id: uuid.UUID
    hours: float
    rate: float
    entry_date: date
    description: str | None
    created_at: datetime


class WorkLogDetailPublic(SQLModel):
    id: uuid.UUID
    item_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    total_amount: float
    created_at: datetime
    task_title: str
    freelancer_email: str
    time_entries: list[TimeEntryPublic]


class WorkLogListItemPublic(SQLModel):
    id: uuid.UUID
    item_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    total_amount: float
    created_at: datetime
    task_title: str
    freelancer_email: str
    payment_batch_id: uuid.UUID | None = None


class WorkLogsPublic(SQLModel):
    data: list[WorkLogListItemPublic]
    count: int


class PaymentBatchCreate(SQLModel):
    """worklog_ids: list of worklog IDs to include in payment (after user excludes)."""

    worklog_ids: list[uuid.UUID] = []

    @field_validator("worklog_ids")
    @classmethod
    def validate_worklog_ids(cls, v: list) -> list:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("must be a list")
        return v


class PaymentBatchPublic(SQLModel):
    id: uuid.UUID
    total_amount: float
    status: str
    created_at: datetime
    worklog_count: int


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
