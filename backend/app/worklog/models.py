from datetime import date, datetime

from sqlmodel import Field, SQLModel


class Freelancer(SQLModel, table=True):
    """freelancer table - stores freelancer information."""

    __tablename__ = "freelancer"

    id: int = Field(primary_key=True)
    name: str = Field(max_length=255)
    email: str = Field(max_length=255, index=True)
    hourly_rate: float = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class WorkLog(SQLModel, table=True):
    """worklog table - consolidated worklog and time_entry records.

    type: 'worklog' or 'time_entry'
    parent_id: self-ref, for time_entry points to worklog id
    freelancer_id: FK to freelancer, only for type='worklog'
    task_name: only for type='worklog'
    description: only for type='worklog'
    start_time: only for type='time_entry'
    end_time: only for type='time_entry'
    hours: only for type='time_entry'
    status: 'pending' or 'paid', only for type='worklog'
    payment_id: FK to payment, only for type='worklog'
    """

    __tablename__ = "worklog"

    id: int = Field(primary_key=True)
    type: str = Field(max_length=50, index=True)
    parent_id: int | None = Field(default=None, foreign_key="worklog.id", index=True)
    freelancer_id: int | None = Field(
        default=None, foreign_key="freelancer.id", index=True
    )
    task_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    start_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(default=None)
    hours: float | None = Field(default=None)
    status: str | None = Field(default=None, max_length=50, index=True)
    payment_id: int | None = Field(default=None, foreign_key="payment.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Payment(SQLModel, table=True):
    """payment table - payment batches for worklogs."""

    __tablename__ = "payment"

    id: int = Field(primary_key=True)
    status: str = Field(max_length=50, index=True)
    total_amount: float = Field(default=0.0)
    date_range_start: date = Field()
    date_range_end: date = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
