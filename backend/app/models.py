import uuid

from datetime import datetime, date

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


class TimeEntryBase(SQLModel):
    start_time: datetime
    end_time: datetime
    rate_per_hour: float = Field(gt=0)
    notes: str | None = Field(default=None, max_length=255)


class TimeEntry(TimeEntryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False)


class TimeEntryPublic(TimeEntryBase):
    id: uuid.UUID
    amount: float


class TimeEntriesPublic(SQLModel):
    data: list[TimeEntryPublic]
    count: int


class TimeEntryCreate(TimeEntryBase):
    pass


class WorklogBase(SQLModel):
    task_name: str = Field(min_length=1, max_length=255)
    freelancer_id: uuid.UUID
    status: str = Field(default="pending", max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Worklog(WorklogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class WorklogCreate(WorklogBase):
    pass


class WorklogSummary(SQLModel):
    id: uuid.UUID
    task_name: str
    freelancer_id: uuid.UUID
    status: str
    total_amount: float
    first_entry_at: datetime | None = None
    last_entry_at: datetime | None = None


class WorklogsPublic(SQLModel):
    data: list[WorklogSummary]
    count: int


class WorklogDetail(SQLModel):
    id: uuid.UUID
    task_name: str
    freelancer_id: uuid.UUID
    status: str
    total_amount: float
    entries: list[TimeEntryPublic]


class PaymentBatchBase(SQLModel):
    from_date: date
    to_date: date


class PaymentBatch(PaymentBatchBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    total_amount: float
    worklog_ids: str


class PaymentBatchPublic(PaymentBatchBase):
    id: uuid.UUID
    total_amount: float
    worklogs: list[WorklogSummary]


class PaymentBatchCreate(PaymentBatchBase):
    worklog_ids: list[uuid.UUID] | None = None
    exclude_worklog_ids: list[uuid.UUID] | None = None
    exclude_freelancer_ids: list[uuid.UUID] | None = None
