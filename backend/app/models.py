import uuid
from typing import Optional

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from decimal import Decimal
from datetime import datetime
from enum import Enum


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
    worklogs: list["WorkLog"] = Relationship(back_populates="user", cascade_delete=True)
    remittances: list["Remittance"] = Relationship(back_populates="user", cascade_delete=True)


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


class RemittanceStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# WorkLog Models
class WorkLogBase(SQLModel):
    task_name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=500)


class WorkLogCreate(WorkLogBase):
    user_id: uuid.UUID


class WorkLog(WorkLogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    hourly_rate: Optional[float] = Field(default=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User | None = Relationship(back_populates="worklogs")
    time_segments: list["TimeSegment"] = Relationship(back_populates="worklog", cascade_delete=True)
    adjustments: list["Adjustment"] = Relationship(back_populates="worklog", cascade_delete=True)
    remittance_line_items: list["RemittanceLineItem"] = Relationship(back_populates="worklog")


class WorkLogPublic(WorkLogBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    total_hours: float
    total_amount: float
    paid_amount: float
    pending_amount: float
    remittance_status: str
    time_segments_count: int
    adjustments_total: float


# TimeSegment Models
class TimeSegmentBase(SQLModel):
    hours: float = Field(max_digits=10, decimal_places=2)
    description: str | None = Field(default=None, max_length=255)


class TimeSegmentCreate(TimeSegmentBase):
    worklog_id: uuid.UUID


class TimeSegment(TimeSegmentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False, ondelete="CASCADE")
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    worklog: WorkLog | None = Relationship(back_populates="time_segments")


class TimeSegmentPublic(TimeSegmentBase):
    id: uuid.UUID
    worklog_id: uuid.UUID
    recorded_at: datetime


# Adjustment Models
class AdjustmentBase(SQLModel):
    amount: float = Field(max_digits=10, decimal_places=2)
    reason: str = Field(max_length=255)


class AdjustmentCreate(AdjustmentBase):
    worklog_id: uuid.UUID


class Adjustment(AdjustmentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    worklog: WorkLog | None = Relationship(back_populates="adjustments")


class AdjustmentPublic(AdjustmentBase):
    id: uuid.UUID
    worklog_id: uuid.UUID
    created_at: datetime


# Remittance Models
class RemittanceBase(SQLModel):
    settlement_period: str | None = Field(default=None, max_length=50)


class Remittance(RemittanceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    total_amount: float = Field(max_digits=10, decimal_places=2)
    status: RemittanceStatus = Field(default=RemittanceStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User | None = Relationship(back_populates="remittances")
    line_items: list["RemittanceLineItem"] = Relationship(back_populates="remittance", cascade_delete=True)


class RemittanceLineItemBase(SQLModel):
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    description: str | None = Field(default=None, max_length=255)


class RemittanceLineItem(RemittanceLineItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    remittance_id: uuid.UUID = Field(foreign_key="remittance.id", nullable=False, ondelete="CASCADE")
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False, ondelete="RESTRICT")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    remittance: Remittance | None = Relationship(back_populates="line_items")
    worklog: WorkLog | None = Relationship(back_populates="remittance_line_items")


class RemittanceLineItemPublic(RemittanceLineItemBase):
    id: uuid.UUID
    worklog_id: uuid.UUID
    task_name: str


class RemittancePublic(RemittanceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    total_amount: float
    status: RemittanceStatus
    created_at: datetime
    updated_at: datetime
    line_items: list[RemittanceLineItemPublic]


class RemittanceGenerationResponse(SQLModel):
    total_remittances_created: int
    remittances: list[RemittancePublic]


class RemittanceStatusUpdate(SQLModel):
    status: RemittanceStatus


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
