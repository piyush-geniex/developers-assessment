import uuid
from datetime import date, datetime
from decimal import Decimal

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


class WorkLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    task_code: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    segments: list["WorkLogSegment"] = Relationship(back_populates="worklog")
    adjustments: list["WorkLogAdjustment"] = Relationship(back_populates="worklog")


class WorkLogSegment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False)
    work_date: date
    hours: Decimal = Field(gt=Decimal("0"))
    hourly_rate: Decimal = Field(gt=Decimal("0"))
    is_questioned: bool = False
    is_settled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    worklog: WorkLog | None = Relationship(back_populates="segments")


class WorkLogAdjustment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False)
    segment_id: uuid.UUID | None = Field(default=None, foreign_key="worklogsegment.id")
    amount: Decimal
    reason: str = Field(min_length=1, max_length=255)
    effective_date: date
    is_settled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    worklog: WorkLog | None = Relationship(back_populates="adjustments")


class Remittance(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    period_start: date
    period_end: date
    total_amount: Decimal
    status: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GenerateRemittancesRequest(SQLModel):
    period_start: date
    period_end: date


class WorkLogDelta(SQLModel):
    worklog_id: uuid.UUID
    delta_amount: Decimal


class UserRemittanceSummary(SQLModel):
    user_id: uuid.UUID
    period_start: date
    period_end: date
    total_amount: Decimal
    status: str
    worklogs: list[WorkLogDelta]


class GenerateRemittancesResponse(SQLModel):
    remittances: list[UserRemittanceSummary]


class WorkLogSummary(SQLModel):
    worklog_id: uuid.UUID
    user_id: uuid.UUID
    total_amount: Decimal
    remittance_status: str


class WorkLogsPublic(SQLModel):
    data: list[WorkLogSummary]
    count: int


class WorkLogCreate(SQLModel):
    user_id: uuid.UUID
    task_code: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class WorkLogSegmentCreate(SQLModel):
    worklog_id: uuid.UUID
    work_date: date
    hours: Decimal
    hourly_rate: Decimal
    is_questioned: bool = False


class WorkLogAdjustmentCreate(SQLModel):
    worklog_id: uuid.UUID
    segment_id: uuid.UUID | None = None
    amount: Decimal
    reason: str = Field(min_length=1, max_length=255)
    effective_date: date
