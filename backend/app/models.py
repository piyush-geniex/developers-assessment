import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import EmailStr, field_validator, model_validator
from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
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


class CreatedAtMixin(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)


class CreatedUpdatedAtMixin(CreatedAtMixin):
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class WorklogEntryType:
    TIME_SEGMENT = "TIME_SEGMENT"
    ADJUSTMENT = "ADJUSTMENT"


class RemittanceStatus:
    REMITTED = "REMITTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED_NEGATIVE = "SKIPPED_NEGATIVE"


class SettlementRunStatus:
    IN_PROGRESS = "IN_PROGRESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    COMPLETED = "COMPLETED"


class WorklogRemittanceStatus:
    REMITTED = "REMITTED"
    UNREMITTED = "UNREMITTED"


class SettlementRun(CreatedUpdatedAtMixin, table=True):
    __tablename__ = "settlement_run"
    id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )
    idempotency_key: str = Field(
        sa_column=Column(String(128), nullable=False, unique=True, index=True)
    )
    status: str = Field(sa_column=Column(String(32), nullable=False, index=True))
    period_from: date = Field(sa_column=Column(Date, nullable=False, index=True))
    period_to: date = Field(sa_column=Column(Date, nullable=False, index=True))
    started_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=False), default=datetime.utcnow, nullable=False
        )
    )
    finished_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=False), nullable=True)
    )
    meta_json: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )


class Worklog(CreatedAtMixin, table=True):
    __tablename__ = "worklog"
    id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    task_ref: str = Field(sa_column=Column(String(255), nullable=False, index=True))


class WorklogEntry(CreatedAtMixin, table=True):
    __tablename__ = "worklog_entry"
    id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )
    worklog_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("worklog.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    entry_type: str = Field(sa_column=Column(String(32), nullable=False, index=True))
    hours: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(12, 2), nullable=True)
    )
    rate: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(12, 2), nullable=True)
    )
    amount_signed: Decimal = Field(
        sa_column=Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    )
    reason: str | None = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    occurred_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=False), default=datetime.utcnow, nullable=False
        )
    )


class Remittance(CreatedUpdatedAtMixin, table=True):
    __tablename__ = "remittance"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_remittance_user_idempotency_key",
        ),
    )
    id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )
    run_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("settlement_run.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    status: str = Field(sa_column=Column(String(32), nullable=False, index=True))
    total_amount: Decimal = Field(
        sa_column=Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    )
    currency: str = Field(sa_column=Column(String(3), nullable=False, default="USD"))
    idempotency_key: str = Field(
        sa_column=Column(String(128), nullable=False, index=True)
    )
    failure_reason: str | None = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )


class RemittanceLine(CreatedAtMixin, table=True):
    __tablename__ = "remittance_line"
    id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )
    remittance_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("remittance.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    worklog_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("worklog.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    amount: Decimal = Field(
        sa_column=Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    )
    snapshot_note: str | None = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )


class GenerateRemittancesForAllUsersRequest(SQLModel):
    from_date: date
    to_date: date
    idempotency_key: str | None = None

    @field_validator("from_date")
    @classmethod
    def validate_from_date(cls, value: date) -> date:
        if value is None:
            raise ValueError("from_date is required")
        return value

    @field_validator("to_date")
    @classmethod
    def validate_to_date(cls, value: date) -> date:
        if value is None:
            raise ValueError("to_date is required")
        return value

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        v = value.strip()
        if len(v) == 0:
            raise ValueError("idempotency_key cannot be empty")
        if len(v) > 128:
            raise ValueError("idempotency_key too long")
        if not re.match(r"^[A-Za-z0-9_-]+$", v):
            raise ValueError("idempotency_key contains invalid characters")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "GenerateRemittancesForAllUsersRequest":
        if self.from_date > self.to_date:
            raise ValueError("from_date cannot be after to_date")
        return self


class GenerateRemittanceUserResult(SQLModel):
    user_id: uuid.UUID
    remittance_id: int
    status: str
    amount: Decimal
    message: str


class GenerateRemittancesForAllUsersResponse(SQLModel):
    run_id: int
    run_status: str
    idempotency_key: str
    remitted_count: int
    failed_count: int
    cancelled_count: int
    skipped_negative_count: int
    results: list[GenerateRemittanceUserResult]


class WorklogAmountsPublic(SQLModel):
    worklog_id: int
    user_id: uuid.UUID
    task_ref: str
    gross_amount: Decimal
    remitted_amount: Decimal
    unremitted_amount: Decimal
    remittance_status: str


class WorklogsAmountsPublic(SQLModel):
    data: list[WorklogAmountsPublic]
    count: int
