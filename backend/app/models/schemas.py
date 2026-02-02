"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
import uuid


# ==================== Freelancer Schemas ====================

class FreelancerRead(BaseModel):
    """Freelancer response schema"""
    id: uuid.UUID
    name: str
    email: str
    hourly_rate: Decimal
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== Task Schemas ====================

class TaskRead(BaseModel):
    """Task response schema"""
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== TimeEntry Schemas ====================

class TimeEntryRead(BaseModel):
    """Time entry response schema"""
    id: uuid.UUID
    worklog_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    hours: Decimal
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== Worklog Schemas ====================

class WorklogRead(BaseModel):
    """Worklog response schema (list view)"""
    id: uuid.UUID
    freelancer_id: uuid.UUID
    task_id: uuid.UUID
    description: Optional[str] = None
    total_hours: Decimal
    total_amount: Decimal
    status: str
    created_at: Optional[datetime] = None
    
    # Joined fields
    freelancer_name: Optional[str] = None
    freelancer_email: Optional[str] = None
    freelancer_hourly_rate: Optional[Decimal] = None
    task_title: Optional[str] = None
    time_entries_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class WorklogWithDetails(BaseModel):
    """Worklog with full time entry details"""
    id: uuid.UUID
    freelancer_id: uuid.UUID
    task_id: uuid.UUID
    description: Optional[str] = None
    total_hours: Decimal
    total_amount: Decimal
    status: str
    created_at: Optional[datetime] = None
    
    # Joined fields
    freelancer: Optional[FreelancerRead] = None
    task: Optional[TaskRead] = None
    time_entries: List[TimeEntryRead] = []
    
    class Config:
        from_attributes = True


# ==================== Payment Schemas ====================

class PaymentRead(BaseModel):
    """Payment response schema"""
    id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    worklog_id: uuid.UUID
    freelancer_id: uuid.UUID
    amount: Decimal
    status: str
    created_at: Optional[datetime] = None
    
    # Joined fields
    freelancer_name: Optional[str] = None
    worklog_description: Optional[str] = None
    task_title: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaymentBatchRead(BaseModel):
    """Payment batch response schema"""
    id: uuid.UUID
    date_from: date
    date_to: date
    total_amount: Decimal
    status: str
    created_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    payments_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class PaymentBatchWithPayments(BaseModel):
    """Payment batch with all payment details"""
    id: uuid.UUID
    date_from: date
    date_to: date
    total_amount: Decimal
    status: str
    created_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    payments: List[PaymentRead] = []
    
    class Config:
        from_attributes = True


# ==================== Request Schemas ====================

class WorklogFilterParams(BaseModel):
    """Parameters for filtering worklogs"""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[str] = None
    freelancer_id: Optional[uuid.UUID] = None


class PaymentPreviewRequest(BaseModel):
    """Request to preview a payment batch"""
    date_from: date
    date_to: date
    excluded_worklog_ids: List[uuid.UUID] = Field(default_factory=list)
    excluded_freelancer_ids: List[uuid.UUID] = Field(default_factory=list)


class PaymentPreviewResponse(BaseModel):
    """Response for payment preview"""
    date_from: date
    date_to: date
    worklogs: List[WorklogRead]
    total_amount: Decimal
    total_worklogs: int
    freelancers_count: int
    excluded_worklog_ids: List[uuid.UUID]
    excluded_freelancer_ids: List[uuid.UUID]


class PaymentProcessRequest(BaseModel):
    """Request to process a payment batch"""
    date_from: date
    date_to: date
    excluded_worklog_ids: List[uuid.UUID] = Field(default_factory=list)
    excluded_freelancer_ids: List[uuid.UUID] = Field(default_factory=list)


class PaymentProcessResponse(BaseModel):
    """Response for processed payment batch"""
    batch: PaymentBatchRead
    payments: List[PaymentRead]
    total_amount: Decimal
    worklogs_paid: int
    freelancers_paid: int
