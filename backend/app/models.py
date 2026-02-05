import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from datetime import date
from typing import List

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

# --- Core Models ---

class FreelancerBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    email: EmailStr = Field(unique=True, index=True, max_length=255)

class Freelancer(FreelancerBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklogs: List["WorkLog"] = Relationship(back_populates="freelancer")

class WorkLogBase(SQLModel):
    task_name: str = Field(max_length=255)
    hourly_rate: float
    status: str = Field(default="pending", max_length=50)

class WorkLog(WorkLogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    freelancer_id: uuid.UUID = Field(foreign_key="freelancer.id", nullable=False)
    
    freelancer: Freelancer = Relationship(back_populates="worklogs")
    time_entries: List["TimeEntry"] = Relationship(back_populates="worklog")

class TimeEntry(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False)
    date: date
    hours: float
    description: str = Field(max_length=255)
    
    worklog: WorkLog = Relationship(back_populates="time_entries")

# --- DTOs / API Schemas ---

class TimeEntryPublic(SQLModel):
    date: date
    hours: float
    description: str

class WorkLogPublic(WorkLogBase):
    id: uuid.UUID
    freelancer_name: str
    total_hours: float
    total_amount: float
    time_entries: List[TimeEntryPublic] = []

class WorkLogsPublic(SQLModel):
    data: List[WorkLogPublic]
    count: int