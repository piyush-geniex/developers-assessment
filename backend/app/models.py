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


class Task(SQLModel, table=True):
    __tablename__ = "task"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class PaymentBatch(SQLModel, table=True):
    __tablename__ = "payment_batch"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    total_amount: float = Field(default=0.0)
    worklog_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    worklogs: list["Worklog"] = Relationship(back_populates="payment_batch")


class Worklog(SQLModel, table=True):
    __tablename__ = "worklog"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="task.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    amount_earned: float = Field(default=0.0)
    status: str = Field(default="pending", max_length=64, index=True)
    payment_batch_id: uuid.UUID | None = Field(
        default=None, foreign_key="payment_batch.id", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    task: Task | None = Relationship()
    owner: User | None = Relationship()
    payment_batch: PaymentBatch | None = Relationship(back_populates="worklogs")
    time_entries: list["TimeEntry"] = Relationship(back_populates="worklog", cascade_delete=True)


class TimeEntry(SQLModel, table=True):
    __tablename__ = "time_entry"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", index=True)
    description: str | None = Field(default=None, max_length=1024)
    hours: float = Field()
    rate: float = Field()
    amount: float = Field()
    logged_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    worklog: Worklog | None = Relationship(back_populates="time_entries")
