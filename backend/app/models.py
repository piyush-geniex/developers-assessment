import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import EmailStr, computed_field
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel


# ============================================================================
# ENUMS
# ============================================================================

class WorkLogStatus(str, Enum):
    """Status workflow for work logs"""
    PENDING = "pending"       # Logged but not reviewed
    APPROVED = "approved"     # Ready for payment
    PAID = "paid"            # Processed
    REJECTED = "rejected"    # Needs correction


class PaymentBatchStatus(str, Enum):
    """Status for payment batches"""
    DRAFT = "draft"           # Being prepared
    PROCESSING = "processing" # In progress
    COMPLETED = "completed"   # Successfully processed
    FAILED = "failed"         # Failed to process


# ============================================================================
# FREELANCER MODELS
# ============================================================================

class FreelancerBase(SQLModel):
    name: str = Field(max_length=255, min_length=1)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    hourly_rate: Decimal = Field(default=Decimal("50.00"), decimal_places=2, ge=0)
    is_active: bool = True


class FreelancerCreate(FreelancerBase):
    password: str | None = Field(default=None, min_length=8, max_length=128)


class FreelancerRegister(SQLModel):
    """Self-registration for freelancers"""
    name: str = Field(max_length=255, min_length=1)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    hourly_rate: Decimal = Field(default=Decimal("50.00"), decimal_places=2, ge=0)


class FreelancerUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255, min_length=1)
    email: EmailStr | None = Field(default=None, max_length=255)
    hourly_rate: Decimal | None = Field(default=None, decimal_places=2, ge=0)
    is_active: bool | None = None


class Freelancer(FreelancerBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str | None = Field(default=None)  # Nullable for migration
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    worklogs: list["WorkLog"] = Relationship(back_populates="freelancer", cascade_delete=True)


class FreelancerPublic(FreelancerBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FreelancersPublic(SQLModel):
    data: list[FreelancerPublic]
    count: int


# ============================================================================
# PAYMENT BATCH MODELS
# ============================================================================

class PaymentBatchBase(SQLModel):
    notes: str | None = Field(default=None, max_length=500)


class PaymentBatchCreate(PaymentBatchBase):
    worklog_ids: list[uuid.UUID]


class PaymentBatch(PaymentBatchBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processed_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    total_amount: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    status: PaymentBatchStatus = Field(
        default=PaymentBatchStatus.COMPLETED,
        sa_type=SAEnum(PaymentBatchStatus, values_callable=lambda x: [e.value for e in x]),
    )

    # Relationships
    processed_by: "User" = Relationship()
    worklogs: list["WorkLog"] = Relationship(back_populates="payment_batch")


class PaymentBatchPublic(PaymentBatchBase):
    id: uuid.UUID
    processed_at: datetime
    processed_by_id: uuid.UUID
    total_amount: Decimal
    status: PaymentBatchStatus
    worklog_count: int | None = None


class PaymentBatchesPublic(SQLModel):
    data: list[PaymentBatchPublic]
    count: int


class PaymentBatchDetail(PaymentBatchPublic):
    worklogs: list["WorkLogPublic"] = []


# ============================================================================
# WORKLOG MODELS
# ============================================================================

class WorkLogBase(SQLModel):
    task_description: str = Field(max_length=500, min_length=1)


class WorkLogCreate(WorkLogBase):
    freelancer_id: uuid.UUID


class WorkLogUpdate(SQLModel):
    task_description: str | None = Field(default=None, max_length=500, min_length=1)
    status: WorkLogStatus | None = None


class WorkLog(WorkLogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    freelancer_id: uuid.UUID = Field(foreign_key="freelancer.id", nullable=False, index=True)
    status: WorkLogStatus = Field(
        default=WorkLogStatus.PENDING,
        index=True,
        sa_type=SAEnum(WorkLogStatus, values_callable=lambda x: [e.value for e in x]),
    )
    payment_batch_id: uuid.UUID | None = Field(default=None, foreign_key="paymentbatch.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    freelancer: Freelancer = Relationship(back_populates="worklogs")
    time_entries: list["TimeEntry"] = Relationship(back_populates="worklog", cascade_delete=True)
    payment_batch: PaymentBatch | None = Relationship(back_populates="worklogs")


class WorkLogPublic(WorkLogBase):
    id: uuid.UUID
    freelancer_id: uuid.UUID
    status: WorkLogStatus
    payment_batch_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class WorkLogsPublic(SQLModel):
    data: list[WorkLogPublic]
    count: int


class WorkLogDetail(WorkLogPublic):
    freelancer: FreelancerPublic
    time_entries: list["TimeEntryPublic"] = []
    total_duration_minutes: int = 0
    total_amount: Decimal = Decimal("0.00")


# ============================================================================
# TIME ENTRY MODELS
# ============================================================================

class TimeEntryBase(SQLModel):
    start_time: datetime
    end_time: datetime
    notes: str | None = Field(default=None, max_length=255)


class TimeEntryCreate(TimeEntryBase):
    work_log_id: uuid.UUID


class TimeEntryUpdate(SQLModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    notes: str | None = Field(default=None, max_length=255)


class TimeEntry(TimeEntryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    work_log_id: uuid.UUID = Field(foreign_key="worklog.id", nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    worklog: WorkLog = Relationship(back_populates="time_entries")

    @computed_field
    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes"""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0


class TimeEntryPublic(TimeEntryBase):
    id: uuid.UUID
    work_log_id: uuid.UUID
    duration_minutes: int
    created_at: datetime


class TimeEntriesPublic(SQLModel):
    data: list[TimeEntryPublic]
    count: int


# ============================================================================
# AGGREGATED / DTO MODELS (for dashboard)
# ============================================================================

class WorkLogSummary(SQLModel):
    """Aggregated worklog for dashboard display"""
    id: uuid.UUID
    task_description: str
    freelancer_id: uuid.UUID
    freelancer_name: str
    freelancer_email: str
    hourly_rate: Decimal
    status: WorkLogStatus
    created_at: datetime
    total_duration_minutes: int
    total_amount: Decimal
    time_entry_count: int


class WorkLogsSummaryPublic(SQLModel):
    data: list[WorkLogSummary]
    count: int


class FreelancerPaymentSummary(SQLModel):
    """Payment summary grouped by freelancer"""
    freelancer_id: uuid.UUID
    freelancer_name: str
    freelancer_email: str
    hourly_rate: Decimal
    worklog_count: int
    total_duration_minutes: int
    total_amount: Decimal
    worklogs: list[WorkLogSummary]


class PaymentIssue(SQLModel):
    """Issues found during payment validation"""
    worklog_id: uuid.UUID
    issue_type: str  # "ZERO_DURATION", "ALREADY_PAID", etc.
    message: str


class PaymentPreviewResponse(SQLModel):
    """Preview response before confirming payment"""
    total_worklogs: int
    total_amount: Decimal
    freelancer_breakdown: list[FreelancerPaymentSummary]
    issues: list[PaymentIssue]
    can_process: bool


class PaymentProcessRequest(SQLModel):
    """Request to process payment"""
    worklog_ids: list[uuid.UUID]
    notes: str | None = None


class PaymentProcessResponse(SQLModel):
    """Response after processing payment"""
    batch_id: uuid.UUID
    total_worklogs: int
    total_amount: Decimal
    status: PaymentBatchStatus


# ============================================================================
# USER MODELS (existing)
# ============================================================================

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


# ============================================================================
# FREELANCER AUTH MODELS
# ============================================================================

class FreelancerToken(SQLModel):
    """JWT token response for freelancer auth"""
    access_token: str
    token_type: str = "bearer"


class FreelancerTokenPayload(SQLModel):
    """Contents of freelancer JWT token"""
    sub: str | None = None
    type: str = "freelancer"


class FreelancerPublicMe(FreelancerBase):
    """Extended public model for authenticated freelancer (includes more fields)"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FreelancerUpdateMe(SQLModel):
    """Fields a freelancer can update about themselves"""
    name: str | None = Field(default=None, max_length=255, min_length=1)
    hourly_rate: Decimal | None = Field(default=None, decimal_places=2, ge=0)


class FreelancerUpdatePassword(SQLModel):
    """Password change for freelancer"""
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# ============================================================================
# FREELANCER PORTAL MODELS
# ============================================================================

class FreelancerTimeEntryCreate(SQLModel):
    """Time entry created by freelancer (no work_log_id needed)"""
    start_time: datetime
    end_time: datetime
    notes: str | None = Field(default=None, max_length=255)


class FreelancerWorkLogCreate(SQLModel):
    """WorkLog created by freelancer - includes time entries"""
    task_description: str = Field(max_length=500, min_length=1)
    time_entries: list[FreelancerTimeEntryCreate] = Field(min_length=1)


class FreelancerWorkLogUpdate(SQLModel):
    """WorkLog update by freelancer (only if PENDING)"""
    task_description: str | None = Field(default=None, max_length=500, min_length=1)


class FreelancerDashboardStats(SQLModel):
    """Stats for freelancer dashboard"""
    total_worklogs: int
    pending_worklogs: int
    approved_worklogs: int
    paid_worklogs: int
    rejected_worklogs: int
    total_hours_logged: Decimal
    total_earned: Decimal
    pending_amount: Decimal


class FreelancerPaymentInfo(SQLModel):
    """Payment info visible to freelancer"""
    batch_id: uuid.UUID
    processed_at: datetime
    total_amount: Decimal
    worklog_count: int
    notes: str | None
    status: PaymentBatchStatus
