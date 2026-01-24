import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, DateTime, func


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
    __tablename__ = "user"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Compensation domain models


class SettlementStatus(str, Enum):
    UNREMITTED = "UNREMITTED"
    REMITTED = "REMITTED"


class TimeSegmentState(str, Enum):
    RECORDED = "RECORDED"
    REMOVED = "REMOVED"


class AdjustmentType(str, Enum):
    CREDIT = "CREDIT"
    DEDUCTION = "DEDUCTION"


class RemittanceStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RemittanceLineSource(str, Enum):
    TIME_SEGMENT = "TIME_SEGMENT"
    ADJUSTMENT = "ADJUSTMENT"


def utc_now() -> datetime:
    return datetime.utcnow()


class WorkLogBase(SQLModel):
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    hourly_rate_cents: int = Field(gt=0, description="Hourly rate in cents")


class WorkLog(WorkLogBase, table=True):
    __tablename__ = "worklog"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    segments: list["TimeSegment"] = Relationship(
        back_populates="worklog", cascade_delete=True
    )
    adjustments: list["Adjustment"] = Relationship(
        back_populates="worklog", cascade_delete=True
    )


class TimeSegmentBase(SQLModel):
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    started_at: datetime
    ended_at: datetime
    minutes: int = Field(gt=0, description="Duration of the segment in minutes")
    hourly_rate_cents: int = Field(gt=0, description="Hourly rate in cents")
    amount_cents: int = Field(gt=0, description="Monetary value of this segment")
    status: TimeSegmentState = Field(default=TimeSegmentState.RECORDED)
    settlement_status: SettlementStatus = Field(default=SettlementStatus.UNREMITTED)
    remittance_id: uuid.UUID | None = Field(default=None, foreign_key="remittance.id")
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class TimeSegment(TimeSegmentBase, table=True):
    __tablename__ = "time_segment"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog: WorkLog | None = Relationship(back_populates="segments")


class AdjustmentBase(SQLModel):
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    amount_cents: int = Field(description="Positive for credit, negative for deduction")
    reason: str | None = Field(default=None, max_length=500)
    adjustment_type: AdjustmentType = Field(default=AdjustmentType.CREDIT)
    settlement_status: SettlementStatus = Field(default=SettlementStatus.UNREMITTED)
    remittance_id: uuid.UUID | None = Field(default=None, foreign_key="remittance.id")
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class Adjustment(AdjustmentBase, table=True):
    __tablename__ = "adjustment"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog: WorkLog | None = Relationship(back_populates="adjustments")


class RemittanceBase(SQLModel):
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    period_start: date
    period_end: date
    status: RemittanceStatus = Field(default=RemittanceStatus.PENDING)
    gross_amount_cents: int = 0
    net_amount_cents: int = 0
    failure_reason: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    finalized_at: datetime | None = Field(default=None)


class Remittance(RemittanceBase, table=True):
    __tablename__ = "remittance"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class RemittanceLine(SQLModel, table=True):
    __tablename__ = "remittance_line"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    remittance_id: uuid.UUID = Field(foreign_key="remittance.id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False)
    source_id: uuid.UUID
    source_type: RemittanceLineSource
    amount_cents: int
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
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
    __tablename__ = "item"
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
