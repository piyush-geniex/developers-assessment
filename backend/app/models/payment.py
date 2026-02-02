"""
Payment and PaymentBatch models
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
import uuid


class PaymentBatch(SQLModel, table=True):
    """Batch of payments processed together"""
    
    __tablename__ = "payment_batches"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    date_from: date = Field(nullable=False)
    date_to: date = Field(nullable=False)
    total_amount: Decimal = Field(default=Decimal("0"), decimal_places=2)
    status: str = Field(default="pending", max_length=50)  # pending, processing, completed, failed
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(default=None)


class Payment(SQLModel, table=True):
    """Individual payment for a worklog"""
    
    __tablename__ = "payments"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    batch_id: Optional[uuid.UUID] = Field(foreign_key="payment_batches.id", default=None)
    worklog_id: uuid.UUID = Field(foreign_key="worklogs.id", nullable=False)
    freelancer_id: uuid.UUID = Field(foreign_key="freelancers.id", nullable=False)
    amount: Decimal = Field(decimal_places=2, nullable=False)
    status: str = Field(default="pending", max_length=50)  # pending, completed, failed
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
