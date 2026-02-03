import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class WorkLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    task_name: str
    amount: float
    created_at: datetime
    remittance_status: str  # REMITTED or UNREMITTED

    @field_validator("remittance_status")
    @classmethod
    def validate_remittance_status(cls, value: str) -> str:
        if value is None:
            raise ValueError("remittance_status is required")
        
        if not isinstance(value, str):
            raise ValueError("remittance_status must be a string")
        
        value = value.strip().upper()
        
        if value not in ["REMITTED", "UNREMITTED"]:
            raise ValueError("remittance_status must be REMITTED or UNREMITTED")
        
        return value


class WorkLogsListResponse(BaseModel):
    data: list[WorkLogResponse]
    count: int


class RemittanceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    period_start: datetime
    period_end: datetime
    status: str
    created_at: datetime
    completed_at: Optional[datetime]


class RemittancesGenerateResponse(BaseModel):
    data: list[RemittanceResponse]
    count: int
    total_amount: float
