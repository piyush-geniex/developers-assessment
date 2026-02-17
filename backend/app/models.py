import uuid
from datetime import datetime

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


# Task models
class TaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class TaskCreate(TaskBase):
    pass

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


class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    worklogs: list["WorkLog"] = Relationship(back_populates="task", cascade_delete=True)


class TaskPublic(TaskBase):
    id: uuid.UUID
    created_at: datetime


# WorkLog models
class WorkLogBase(SQLModel):
    status: str = Field(default="PENDING", max_length=50)


class WorkLogCreate(SQLModel):
    task_id: uuid.UUID
    freelancer_id: uuid.UUID
    status: str = Field(default="PENDING", max_length=50)


class WorkLog(WorkLogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(
        foreign_key="task.id", nullable=False, ondelete="CASCADE", index=True
    )
    freelancer_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    task: Task | None = Relationship(back_populates="worklogs")
    freelancer: User | None = Relationship()
    time_entries: list["TimeEntry"] = Relationship(
        back_populates="worklog", cascade_delete=True
    )
    payments: list["Payment"] = Relationship(back_populates="worklog")


class WorkLogPublic(WorkLogBase):
    id: uuid.UUID
    task_id: uuid.UUID
    freelancer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    total_earnings: float | None = None
    task: TaskPublic | None = None
    freelancer: UserPublic | None = None


class WorkLogDetail(WorkLogPublic):
    time_entries: list["TimeEntryPublic"] = []


class WorkLogsPublic(SQLModel):
    data: list[WorkLogPublic]
    count: int


# TimeEntry models
class TimeEntryBase(SQLModel):
    hours: float = Field(gt=0)
    rate: float = Field(ge=0)
    description: str | None = Field(default=None, max_length=1000)
    entry_date: datetime


class TimeEntryCreate(TimeEntryBase):
    worklog_id: uuid.UUID


class TimeEntry(TimeEntryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(
        foreign_key="worklog.id", nullable=False, ondelete="CASCADE", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    worklog: WorkLog | None = Relationship(back_populates="time_entries")


class TimeEntryPublic(TimeEntryBase):
    id: uuid.UUID
    worklog_id: uuid.UUID
    created_at: datetime
    earnings: float | None = None


# PaymentBatch models
class PaymentBatchBase(SQLModel):
    status: str = Field(default="PENDING", max_length=50)
    start_date: datetime
    end_date: datetime
    notes: str | None = Field(default=None, max_length=1000)


class PaymentBatchCreate(PaymentBatchBase):
    excluded_worklog_ids: list[uuid.UUID] = []
    excluded_freelancer_ids: list[uuid.UUID] = []

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("start_date is required")
        if not isinstance(value, datetime):
            raise ValueError("start_date must be a datetime")
        return value

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("end_date is required")
        if not isinstance(value, datetime):
            raise ValueError("end_date must be a datetime")
        return value


class PaymentBatch(PaymentBatchBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    processed_at: datetime | None = None
    total_amount: float = Field(default=0.0)
    payments: list["Payment"] = Relationship(back_populates="payment_batch")


class PaymentBatchPublic(PaymentBatchBase):
    id: uuid.UUID
    created_at: datetime
    processed_at: datetime | None
    total_amount: float
    payment_count: int | None = None


class PaymentBatchDetail(PaymentBatchPublic):
    payments: list["PaymentPublic"] = []


# Payment models
class PaymentBase(SQLModel):
    amount: float = Field(ge=0)
    status: str = Field(default="PENDING", max_length=50)


class Payment(PaymentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(
        foreign_key="worklog.id", nullable=False, ondelete="CASCADE", index=True
    )
    payment_batch_id: uuid.UUID = Field(
        foreign_key="paymentbatch.id", nullable=False, ondelete="CASCADE", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    processed_at: datetime | None = None
    worklog: WorkLog | None = Relationship(back_populates="payments")
    payment_batch: PaymentBatch | None = Relationship(back_populates="payments")


class PaymentPublic(PaymentBase):
    id: uuid.UUID
    worklog_id: uuid.UUID
    payment_batch_id: uuid.UUID
    created_at: datetime
    processed_at: datetime | None
    worklog: WorkLogPublic | None = None
