from uuid import UUID
from enum import Enum
from typing import Optional
from datetime import date
from pydantic import BaseModel
from datetime import date, datetime, timezone
from typing import Annotated, List, Optional
import uuid
from app.schemas import RemittanceStatus
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Enum
from sqlmodel import SQLModel, Field, Relationship

# Shared properties


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = True
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
    email: EmailStr | None = Field(
        default=None, max_length=255)  # type: ignore
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
    items: list["Item"] = Relationship(
        back_populates="owner", cascade_delete=True)
    # relationships addded
    worklogs: list["WorkLog"] = Relationship(
        back_populates="user", cascade_delete=True)
    remittances: list["Remittance"] = Relationship(
        back_populates="user", cascade_delete=True)

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
    title: str | None = Field(
        default=None, min_length=1, max_length=255)  # type: ignore


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


# implementation
class Adjustment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: UUID = Field(foreign_key="worklog.id")
    description: str
    amount: float

    worklog: "WorkLog" = Relationship(back_populates="adjustments")


class TimeSegment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: UUID = Field(foreign_key="worklog.id")
    start: datetime
    end: datetime

    worklog: "WorkLog" = Relationship(back_populates="time_segments")


class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str
    worklogs: List["WorkLog"] = Relationship(back_populates="task")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class WorkLog(SQLModel, table=True):
    """
    Container for all work done against a task by a user.
    Work is tracked via time_segments and adjustments.
    """
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    task_id: UUID = Field(foreign_key="task.id", index=True)
    created_at: datetime = Field(datetime.now(timezone.utc))
    updated_at: datetime = Field(datetime.now(timezone.utc))

    # Relationships
    user: "User" = Relationship(back_populates="worklogs")
    task: Task = Relationship(back_populates="worklogs")
    time_segments: List[TimeSegment] = Relationship(
        back_populates="worklog",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    adjustments: List[Adjustment] = Relationship(
        back_populates="worklog",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    remittance_worklogs: List["RemittanceWorkLog"] = Relationship(
        back_populates="worklog"
    )


class Remittance(SQLModel, table=True):
    """
    A single payout (settlement) for a user covering a time period.
    Groups multiple worklogs into one payment batch.
    """
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    total_amount: float = Field(description="Total amount to be paid")
    status: str = Field(
        default=RemittanceStatus.remitted,
    )
    period_start: date = Field(description="Start of settlement period")
    period_end: date = Field(description="End of settlement period")
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    paid_at: Optional[datetime] = Field(
        default=None,
        description="When payment was completed"
    )

    # Relationships
    user: "User" = Relationship(back_populates="remittances")
    remittance_worklogs: List["RemittanceWorkLog"] = Relationship(
        back_populates="remittance",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class RemittanceWorkLog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    remittance_id: UUID = Field(foreign_key="remittance.id")
    worklog_id: UUID = Field(foreign_key="worklog.id")
    amount: float
    remittance: "Remittance" = Relationship(
        back_populates="remittance_worklogs")
    worklog: "WorkLog" = Relationship(back_populates="remittance_worklogs")
