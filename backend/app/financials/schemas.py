import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.financials.models import RemittanceState, TransactionType


# Wallet Schemas
class WalletPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    balance: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


# Transaction Schemas
class TransactionPublic(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    amount: Decimal
    transaction_type: TransactionType
    description: str | None
    reference_id: uuid.UUID | None
    created_at: datetime


class TransactionsPublic(BaseModel):
    data: list[TransactionPublic]
    count: int


# Remittance Schemas
class RemittanceBase(BaseModel):
    amount: Decimal
    status: RemittanceState


class RemittancePublic(RemittanceBase):
    id: uuid.UUID
    worker_id: uuid.UUID
    settlement_run_id: uuid.UUID | None
    task_id: uuid.UUID | None
    created_at: datetime
    processed_at: datetime | None


class RemittancesPublic(BaseModel):
    data: list[RemittancePublic]
    count: int


# Settlement Run Schemas
class SettlementRunPublic(BaseModel):
    id: uuid.UUID
    start_date: datetime
    end_date: datetime
    status: str
    created_at: datetime


class GenerateRemittancesResponse(BaseModel):
    settlement_run_id: uuid.UUID
    remittances_created: int
    total_amount: Decimal
