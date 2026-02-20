import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from pydantic import EmailStr
from sqlmodel import DateTime, Field, Relationship, SQLModel


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


# Base model, for task and work log entry models, common fields
class TaskBase(ItemBase):
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="RESTRICT"
    )
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    edited_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    edited_by_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", nullable=True, ondelete="RESTRICT"
    )


class TaskCreate(ItemBase):
    pass


class TaskUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore   
    description: str | None = Field(default=None, max_length=255)


class TaskItem(TaskBase):
    id: uuid.UUID
    created_at: datetime 
    total_amount: Decimal = Field(default=0.0, max_digits=10, decimal_places=2, nullable=True, multiple_of=0.01)


class TaskItems(SQLModel):
    data: list[TaskItem]
    count: int


# Database model, database table inferred from class name
class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, primary_key=True)

# Database model, database table inferred from class name
class WorkLogEntry(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, primary_key=True)
    task_id: uuid.UUID = Field(
        foreign_key="task.id", nullable=False, ondelete="RESTRICT"
    )
    start_time: datetime = Field(sa_type=DateTime(timezone=True))
    end_time: datetime = Field(sa_type=DateTime(timezone=True))
    amount: Decimal = Field(default=Decimal("0.0"), max_digits=10, decimal_places=2)
    approved: bool = False
    approved_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    approved_by_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", nullable=True, ondelete="RESTRICT"
    )
    payment_initiated: bool = False
    payment_initiated_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    initiated_by_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", nullable=True, ondelete="RESTRICT"
    )
    payment_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    paid: bool = False


class WorkLogEntryCreate(TaskCreate):
    task_id: uuid.UUID
    start_time: datetime = Field(default=None, sa_type=DateTime(timezone=True))
    end_time: datetime = Field(default=None, sa_type=DateTime(timezone=True))
    amount: Decimal = Field(default=0.0, max_digits=10, decimal_places=2)


class WorkLogEntryUpdate(WorkLogEntryCreate):
    pass


class WorkLogEntryApprove(SQLModel):
    approved: bool = True


class WorkLogEntryBulkPaymentInitiate(SQLModel):
    entry_ids: List[uuid.UUID]
    
    
class WorkLogEntryBulkDelete(WorkLogEntryBulkPaymentInitiate):
    pass


class WorkLogEntryItem(TaskBase):
    id: uuid.UUID
    task_id: uuid.UUID
    start_time: datetime = Field(sa_type=DateTime(timezone=True))
    end_time: datetime = Field(sa_type=DateTime(timezone=True))
    amount: Decimal
    approved: bool
    approved_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    approved_by_id: uuid.UUID | None
    payment_initiated: bool
    payment_initiated_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    initiated_by_id: uuid.UUID | None
    payment_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    paid: bool


class WorkLogEntries(SQLModel):
    data: list[WorkLogEntryItem]
    count: int
