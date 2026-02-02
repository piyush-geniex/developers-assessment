import enum
import uuid
from typing import Optional

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
    work_logs: list["WorkLog"] = Relationship(back_populates="user", cascade_delete=True)
    remittances: list["Remittance"] = Relationship(
        back_populates="user", cascade_delete=True
    )


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


# --- WorkLog Payment Dashboard models ---

class TaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)


class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    work_logs: list["WorkLog"] = Relationship(back_populates="task", cascade_delete=True)


class TaskPublic(TaskBase):
    id: uuid.UUID


class WorkLog(SQLModel, table=True):
    """Container for all time entries recorded by a freelancer against a task."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="task.id", nullable=False, ondelete="CASCADE")
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    remittance_id: uuid.UUID | None = Field(
        default=None, foreign_key="remittance.id", nullable=True, ondelete="SET NULL"
    )
    task: Task | None = Relationship(back_populates="work_logs")
    user: User | None = Relationship(back_populates="work_logs")
    remittance: Optional["Remittance"] = Relationship(back_populates="work_logs")
    time_entries: list["TimeEntry"] = Relationship(
        back_populates="work_log", cascade_delete=True
    )


class TimeEntry(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    work_log_id: uuid.UUID = Field(
        foreign_key="worklog.id", nullable=False, ondelete="CASCADE"
    )
    entry_date: str = Field(max_length=10)  # ISO date YYYY-MM-DD
    duration_minutes: int = Field(ge=0)
    amount_cents: int = Field(ge=0)
    description: str | None = Field(default=None, max_length=500)
    work_log: WorkLog | None = Relationship(back_populates="time_entries")


class TimeEntryPublic(SQLModel):
    id: uuid.UUID
    work_log_id: uuid.UUID
    entry_date: str
    duration_minutes: int
    amount_cents: int
    description: str | None


class RemittanceStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkLogRemittanceFilter(str, enum.Enum):
    """Query filter for list worklogs: remitted vs unremitted."""
    REMITTED = "REMITTED"
    UNREMITTED = "UNREMITTED"


class Remittance(SQLModel, table=True):
    """Payment batch for a freelancer for a period."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    period_start: str = Field(max_length=10)  # ISO date
    period_end: str = Field(max_length=10)
    status: RemittanceStatus = Field(default=RemittanceStatus.PENDING)
    total_amount_cents: int = Field(default=0, ge=0)
    user: User | None = Relationship(back_populates="remittances")
    work_logs: list[WorkLog] = Relationship(back_populates="remittance")


# API response models for worklogs
class WorkLogListItem(SQLModel):
    id: uuid.UUID
    task_id: uuid.UUID
    task_title: str
    user_id: uuid.UUID
    user_email: str
    user_full_name: str | None
    amount_cents: int
    remittance_id: uuid.UUID | None
    remittance_status: RemittanceStatus | None


class WorkLogsPublic(SQLModel):
    data: list[WorkLogListItem]
    count: int


class WorkLogDetail(WorkLogListItem):
    time_entries: list[TimeEntryPublic]


# Payment batch request/response
class PaymentBatchPreview(SQLModel):
    """Eligible worklogs in date range for payment."""
    work_logs: list[WorkLogListItem]
    total_amount_cents: int
    period_start: str
    period_end: str


class ConfirmPaymentRequest(SQLModel):
    period_start: str
    period_end: str
    include_work_log_ids: list[uuid.UUID]  # worklogs to include (exclude rest)
    exclude_freelancer_ids: list[uuid.UUID] | None = None  # skip these users entirely


class RemittancePublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    period_start: str
    period_end: str
    status: RemittanceStatus
    total_amount_cents: int
