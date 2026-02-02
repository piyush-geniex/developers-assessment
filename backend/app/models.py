from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel, create_engine, Session, select

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    role: str # "admin" or "freelancer"
    
    worklogs: List["WorkLog"] = Relationship(back_populates="freelancer")

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    rate_per_hour: float
    
    worklogs: List["WorkLog"] = Relationship(back_populates="task")

class WorkLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    freelancer_id: int = Field(foreign_key="user.id")
    status: str = Field(default="pending") # "pending", "approved", "paid"
    
    task: Task = Relationship(back_populates="worklogs")
    freelancer: User = Relationship(back_populates="worklogs")
    time_entries: List["TimeEntry"] = Relationship(back_populates="worklog")

class TimeEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    worklog_id: int = Field(foreign_key="worklog.id")
    date: datetime
    hours: float
    description: str
    
    worklog: WorkLog = Relationship(back_populates="time_entries")

class PaymentBatch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_amount: float
    status: str = Field(default="confirmed") # "confirmed"
    # In a real app, you'd link this to specific worklogs via a junction table or by adding payment_batch_id to WorkLog
