import uuid
from datetime import date, datetime

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    hourly_rate: float | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    worklogs: list["Worklog"] = Relationship(back_populates="freelancer", cascade_delete=True)


class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# ---------------------------------------------------------------------------
# Item  (unchanged boilerplate)
# ---------------------------------------------------------------------------

class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# ---------------------------------------------------------------------------
# Worklog  (= task entity owned by a freelancer)
# ---------------------------------------------------------------------------

class WorklogBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class WorklogCreate(WorklogBase):
    pass


class Worklog(WorklogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    freelancer_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True
    )
    hourly_rate: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    freelancer: User | None = Relationship(back_populates="worklogs")
    time_entries: list["TimeEntry"] = Relationship(
        back_populates="worklog", cascade_delete=True
    )


class WorklogPublic(WorklogBase):
    id: uuid.UUID
    freelancer_id: uuid.UUID
    freelancer_name: str | None
    hourly_rate: float
    total_hours: float
    total_earned: float
    created_at: datetime


class WorklogDetail(WorklogPublic):
    time_entries: list["TimeEntryPublic"]


class WorklogsPublic(SQLModel):
    data: list[WorklogPublic]
    count: int


# ---------------------------------------------------------------------------
# TimeEntry
# ---------------------------------------------------------------------------

class TimeEntryBase(SQLModel):
    start_time: datetime
    end_time: datetime
    description: str | None = Field(default=None, max_length=500)


class TimeEntryCreate(TimeEntryBase):
    worklog_id: uuid.UUID


class TimeEntry(TimeEntryBase, table=True):
    __tablename__ = "time_entry"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worklog_id: uuid.UUID = Field(
        foreign_key="worklog.id", nullable=False, ondelete="CASCADE", index=True
    )
    hours: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    worklog: Worklog | None = Relationship(back_populates="time_entries")
    payments: list["Payment"] = Relationship(back_populates="time_entry")


class TimeEntryPublic(TimeEntryBase):
    id: uuid.UUID
    worklog_id: uuid.UUID
    hours: float
    created_at: datetime


# ---------------------------------------------------------------------------
# PaymentBatch
# ---------------------------------------------------------------------------

class PaymentBatchCreate(SQLModel):
    date_from: date
    date_to: date


class PaymentBatch(SQLModel, table=True):
    __tablename__ = "payment_batch"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    date_from: date = Field(index=True)
    date_to: date
    status: str = Field(default="draft")
    created_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    total_amount: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    confirmed_at: datetime | None = None

    payments: list["Payment"] = Relationship(back_populates="batch", cascade_delete=True)


class PaymentBatchPublic(SQLModel):
    id: uuid.UUID
    date_from: date
    date_to: date
    status: str
    created_by_id: uuid.UUID
    total_amount: float | None
    created_at: datetime
    confirmed_at: datetime | None


class EligibleEntry(SQLModel):
    time_entry_id: uuid.UUID
    worklog_id: uuid.UUID
    worklog_title: str
    freelancer_id: uuid.UUID
    freelancer_name: str | None
    hours: float
    hourly_rate: float
    amount: float
    start_time: datetime
    end_time: datetime


class PaymentBatchDetail(PaymentBatchPublic):
    eligible_entries: list[EligibleEntry]
    payment_lines: list[EligibleEntry] = []


class PaymentBatchesPublic(SQLModel):
    data: list[PaymentBatchPublic]
    count: int


class ConfirmBatchIn(SQLModel):
    excluded_worklog_ids: list[uuid.UUID] = Field(default_factory=list)
    excluded_freelancer_ids: list[uuid.UUID] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class Payment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    batch_id: uuid.UUID = Field(
        foreign_key="payment_batch.id", nullable=False, ondelete="CASCADE", index=True
    )
    time_entry_id: uuid.UUID = Field(
        foreign_key="time_entry.id", nullable=False, index=True
    )
    worklog_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False, index=True)
    freelancer_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    hours: float
    hourly_rate: float
    amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    batch: PaymentBatch | None = Relationship(back_populates="payments")
    time_entry: TimeEntry | None = Relationship(back_populates="payments")


class PaymentPublic(SQLModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    time_entry_id: uuid.UUID
    worklog_id: uuid.UUID
    freelancer_id: uuid.UUID
    hours: float
    hourly_rate: float
    amount: float
    created_at: datetime


# ---------------------------------------------------------------------------
# Auth / utility
# ---------------------------------------------------------------------------

class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
