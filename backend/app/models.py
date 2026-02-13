import uuid
from datetime import datetime
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    FREELANCER = "FREELANCER"


class PaymentBatchStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.FREELANCER)
    hourly_rate: float | None = Field(default=None)


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
    time_entries: list["TimeEntry"] = Relationship(back_populates="freelancer", cascade_delete=True)
    created_batches: list["PaymentBatch"] = Relationship(back_populates="creator", cascade_delete=True)
    payments: list["Payment"] = Relationship(back_populates="freelancer", cascade_delete=True)


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


# Task
class TaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    time_entries: list["TimeEntry"] = Relationship(back_populates="task", cascade_delete=True)


class TaskPublic(TaskBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TasksPublic(SQLModel):
    data: list[TaskPublic]
    count: int


# TimeEntry
class TimeEntryBase(SQLModel):
    task_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    description: str | None = Field(default=None)


class TimeEntryCreate(TimeEntryBase):
    pass


class TimeEntryUpdate(SQLModel):
    task_id: uuid.UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    description: str | None = None


class TimeEntry(TimeEntryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="task.id", nullable=False, ondelete="CASCADE")
    freelancer_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    task: Task | None = Relationship(back_populates="time_entries")
    freelancer: User | None = Relationship(back_populates="time_entries")
    payments: list["Payment"] = Relationship(back_populates="time_entry", cascade_delete=True)


class TimeEntryPublic(TimeEntryBase):
    id: uuid.UUID
    freelancer_id: uuid.UUID
    freelancer_name: str
    created_at: datetime
    task_title: str


class TimeEntriesPublic(SQLModel):
    data: list[TimeEntryPublic]
    count: int


# Worklog
class WorklogSummary(SQLModel):
    task_id: uuid.UUID
    task_title: str
    freelancer_id: uuid.UUID
    freelancer_name: str
    total_hours: float
    total_amount: float
    entry_count: int


class WorklogsSummary(SQLModel):
    data: list[WorklogSummary]
    count: int


# PaymentBatch schemas
class PaymentBatchCreate(SQLModel):
    date_from: datetime
    date_to: datetime


class PaymentBatchPublic(SQLModel):
    id: uuid.UUID
    created_by_id: uuid.UUID
    date_from: datetime
    date_to: datetime
    status: PaymentBatchStatus
    total_amount: float
    created_at: datetime
    confirmed_at: datetime | None


class PaymentBatchesPublic(SQLModel):
    data: list[PaymentBatchPublic]
    count: int


# Payment schemas
class PaymentPublic(SQLModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    freelancer_id: uuid.UUID
    freelancer_name: str
    time_entry_id: uuid.UUID
    task_title: str
    hours: float
    hourly_rate: float
    amount: float
    created_at: datetime


class PaymentsPublic(SQLModel):
    data: list[PaymentPublic]
    count: int


# Eligible time entry for payment preview
class EligibleTimeEntry(SQLModel):
    time_entry_id: uuid.UUID
    task_id: uuid.UUID
    task_title: str
    freelancer_id: uuid.UUID
    freelancer_name: str
    start_time: datetime
    end_time: datetime
    hours: float
    hourly_rate: float
    amount: float


class PaymentBatchDetail(SQLModel):
    batch: PaymentBatchPublic
    eligible_entries: list[EligibleTimeEntry]


# PaymentBatch
class PaymentBatch(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")

    date_from: datetime
    date_to: datetime
    status: PaymentBatchStatus = Field(default=PaymentBatchStatus.DRAFT)
    total_amount: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: datetime | None = None

    creator: User | None = Relationship(back_populates="created_batches")
    payments: list["Payment"] = Relationship(back_populates="batch", cascade_delete=True)


# Payment
class Payment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    batch_id: uuid.UUID = Field(foreign_key="paymentbatch.id", nullable=False, ondelete="CASCADE")
    freelancer_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    time_entry_id: uuid.UUID = Field(foreign_key="timeentry.id", nullable=False, ondelete="CASCADE")

    hours: float
    hourly_rate: float
    amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    batch: PaymentBatch | None = Relationship(back_populates="payments")
    freelancer: User | None = Relationship(back_populates="payments")
    time_entry: TimeEntry | None = Relationship(back_populates="payments")
