import uuid
from datetime import datetime

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


# Worklog Payment System Models

# Freelancer Base
class FreelancerBase(SQLModel):
    full_name: str = Field(max_length=255)
    hourly_rate: float = Field(default=0.0)
    status: str = Field(default="active", max_length=50)


# Properties to receive via API on creation
class FreelancerCreate(FreelancerBase):
    pass

# Properties to receive via API on update
class FreelancerUpdate(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    hourly_rate: float | None = Field(default=None)
    status: str | None = Field(default=None, max_length=50)


# Database model
class Freelancer(FreelancerBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


# Properties to return via API
class FreelancerPublic(FreelancerBase):
    id: uuid.UUID
    created_at: datetime


class FreelancersPublic(SQLModel):
    data: list[FreelancerPublic]
    count: int


# WorkLog Base
class WorkLogBase(SQLModel):
    hours: float = Field(default=0.0)
    payment_status: str = Field(default="UNPAID", max_length=50)


# Properties to receive via API on creation
class WorkLogCreate(WorkLogBase):
    freelancer_id: uuid.UUID
    item_id: uuid.UUID


# Properties to receive via API on update
class WorkLogUpdate(SQLModel):
    hours: float | None = Field(default=None)
    payment_status: str | None = Field(default=None, max_length=50)


# Database model
class WorkLog(WorkLogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    freelancer_id: uuid.UUID = Field(foreign_key="freelancer.id", index=True)
    item_id: uuid.UUID = Field(foreign_key="item.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    paid_at: datetime | None = Field(default=None, index=True)


# Properties to return via API
class WorkLogPublic(WorkLogBase):
    id: uuid.UUID
    freelancer_id: uuid.UUID
    item_id: uuid.UUID
    item_title: str
    created_at: datetime
    paid_at: datetime | None


class WorkLogsPublic(SQLModel):
    data: list[WorkLogPublic]
    count: int


# TimeSegment Base
class TimeSegmentBase(SQLModel):
    hours: float = Field(default=0.0)
    segment_date: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = Field(default=None)


# Properties to receive via API on creation
class TimeSegmentCreate(TimeSegmentBase):
    worklog_id: uuid.UUID


# Properties to receive via API on update
class TimeSegmentUpdate(SQLModel):
    hours: float | None = Field(default=None)
    segment_date: datetime | None = Field(default=None)
    notes: str | None = Field(default=None)


# Database model
class TimeSegment(TimeSegmentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", index=True)


# Properties to return via API
class TimeSegmentPublic(TimeSegmentBase):
    id: uuid.UUID
    worklog_id: uuid.UUID


class TimeSegmentsPublic(SQLModel):
    data: list[TimeSegmentPublic]
    count: int

