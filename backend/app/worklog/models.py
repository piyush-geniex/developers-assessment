from datetime import datetime
from sqlmodel import Field, SQLModel


class Freelancer(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str = Field(max_length=255)
    email: str = Field(max_length=255, index=True)
    rate_per_hour: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class WorkLog(SQLModel, table=True):
    id: int = Field(primary_key=True)
    freelancer_id: int = Field(foreign_key="freelancer.id", index=True)
    task_name: str = Field(max_length=255)
    status: str = Field(default="PENDING", index=True)
    total_amount: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TimeEntry(SQLModel, table=True):
    id: int = Field(primary_key=True)
    worklog_id: int = Field(foreign_key="worklog.id", index=True)
    description: str = Field(max_length=500)
    hours: float = Field(default=0.0)
    rate: float = Field(default=0.0)
    amount: float = Field(default=0.0)
    entry_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Payment(SQLModel, table=True):
    id: int = Field(primary_key=True)
    freelancer_id: int = Field(foreign_key="freelancer.id", index=True)
    total_amount: float = Field(default=0.0)
    payment_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    status: str = Field(default="PENDING", index=True)
    worklog_ids: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
