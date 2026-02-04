import uuid
from datetime import date, datetime

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


# WorkLog models
class WorkLogBase(SQLModel):
    task_name: str = Field(max_length=255)
    total_hours: float = Field(default=0.0)
    hourly_rate: float = Field(default=0.0)
    total_amount: float = Field(default=0.0)
    status: str = Field(default="PENDING", max_length=50)


class WorkLogCreate(SQLModel):
    task_name: str = Field(min_length=1, max_length=255)
    freelancer_id: uuid.UUID
    hourly_rate: float = Field(gt=0)


class WorkLogUpdate(SQLModel):
    task_name: str | None = Field(default=None, max_length=255)
    hourly_rate: float | None = Field(default=None, gt=0)
    status: str | None = Field(default=None, max_length=50)


class WorkLog(WorkLogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    freelancer_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    freelancer: User | None = Relationship()
    time_entries: list["TimeEntry"] = Relationship(back_populates="worklog", cascade_delete=True)


class WorkLogPublic(WorkLogBase):
    id: uuid.UUID
    freelancer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class WorkLogsPublic(SQLModel):
    data: list[WorkLogPublic]
    count: int


# TimeEntry models
class TimeEntryBase(SQLModel):
    description: str = Field(max_length=500)
    hours: float = Field(gt=0)
    date: date


class TimeEntryCreate(TimeEntryBase):
    worklog_id: uuid.UUID


class TimeEntryUpdate(SQLModel):
    description: str | None = Field(default=None, max_length=500)
    hours: float | None = Field(default=None, gt=0)
    date: date | None = None


class TimeEntry(TimeEntryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    worklog: WorkLog | None = Relationship(back_populates="time_entries")


class TimeEntryPublic(TimeEntryBase):
    id: uuid.UUID
    worklog_id: uuid.UUID
    created_at: datetime


class TimeEntriesPublic(SQLModel):
    data: list[TimeEntryPublic]
    count: int


# Payment models
class PaymentBase(SQLModel):
    batch_name: str = Field(max_length=255)
    date_from: date
    date_to: date
    total_amount: float = Field(default=0.0)
    status: str = Field(default="DRAFT", max_length=50)


class PaymentCreate(SQLModel):
    batch_name: str = Field(min_length=1, max_length=255)
    date_from: date
    date_to: date
    worklog_ids: list[uuid.UUID]


class PaymentUpdate(SQLModel):
    batch_name: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=50)


class Payment(PaymentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    created_by: User | None = Relationship()
    payment_worklogs: list["PaymentWorkLog"] = Relationship(back_populates="payment", cascade_delete=True)


class PaymentPublic(PaymentBase):
    id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime


class PaymentsPublic(SQLModel):
    data: list[PaymentPublic]
    count: int


# PaymentWorkLog models (junction table)
class PaymentWorkLogBase(SQLModel):
    amount: float


class PaymentWorkLog(PaymentWorkLogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    payment_id: uuid.UUID = Field(foreign_key="payment.id", nullable=False, ondelete="CASCADE")
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False)
    payment: Payment | None = Relationship(back_populates="payment_worklogs")


class PaymentWorkLogPublic(PaymentWorkLogBase):
    id: uuid.UUID
    payment_id: uuid.UUID
    worklog_id: uuid.UUID
