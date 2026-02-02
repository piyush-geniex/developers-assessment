"""
Freelancer model
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class Freelancer(SQLModel, table=True):
    """Freelancer who logs work and receives payments"""
    
    __tablename__ = "freelancers"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    email: str = Field(max_length=255, unique=True, nullable=False)
    hourly_rate: Decimal = Field(default=Decimal("25.00"), decimal_places=2)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
