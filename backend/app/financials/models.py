import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models import User

if TYPE_CHECKING:
    from app.tasks.models import TimeSegment


class RemittanceState(str, Enum):
    PENDING = "PENDING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    OFFSET = "OFFSET"
    AWAITING_FUNDING = "AWAITING_FUNDING"


class AdjustmentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class TaskStatusState(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TransactionType(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class SettlementRun(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID | None = Field(default=None)  # Link to TaskStatus
    start_date: datetime
    end_date: datetime
    status: str = Field(default="PENDING")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    remittances: list["Remittance"] = Relationship(back_populates="settlement_run")


class Remittance(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worker_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    settlement_run_id: uuid.UUID | None = Field(
        default=None, foreign_key="settlementrun.id"
    )
    task_id: uuid.UUID | None = Field(default=None)
    amount: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    status: RemittanceState = Field(default=RemittanceState.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: datetime | None = Field(default=None)

    user: User = Relationship(back_populates="remittances")
    settlement_run: SettlementRun | None = Relationship(back_populates="remittances")
    time_segments: list["TimeSegment"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "foreign(Remittance.id) == remote(TimeSegment.remittance_id)",
            "uselist": True,
        }
    )
    adjustments: list["Adjustment"] = Relationship(back_populates="remittance")


class Adjustment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    time_segment_id: uuid.UUID = Field(nullable=False)
    remittance_id: uuid.UUID | None = Field(default=None, foreign_key="remittance.id")
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    reason: str
    status: AdjustmentStatus = Field(default=AdjustmentStatus.PENDING)
    effective_date: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    remittance: Remittance | None = Relationship(back_populates="adjustments")


class Wallet(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, unique=True)
    balance: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    reserve: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    transactions: list["Transaction"] = Relationship(back_populates="wallet")

    def credit(self, amount: Decimal, reserve: bool = False):
        if amount < 0:
            raise ValueError("Credit amount must be positive")
        if reserve:
            self.reserve += amount
        else:
            self.balance += amount

    def debit(self, amount: Decimal, reserve: bool = False):
        if amount < 0:
            raise ValueError("Debit amount must be positive")
        if reserve:
            if self.reserve < amount:
                raise ValueError("Insufficient reserve funds")
            self.reserve -= amount
        else:
            if self.balance < amount:
                raise ValueError("Insufficient funds")
            self.balance -= amount


class Transaction(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    wallet_id: uuid.UUID = Field(foreign_key="wallet.id", nullable=False)
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    transaction_type: TransactionType
    description: str | None = None
    reference_id: uuid.UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    wallet: Wallet = Relationship(back_populates="transactions")


class TaskStatus(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_type: str
    status: TaskStatusState = Field(default=TaskStatusState.PENDING)
    progress_percentage: int = Field(default=0)
    message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
