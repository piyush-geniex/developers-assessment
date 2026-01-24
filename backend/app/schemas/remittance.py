import uuid
from datetime import date, datetime

from pydantic import computed_field
from sqlmodel import SQLModel

from app.models import (
    AdjustmentBase,
    AdjustmentType,
    RemittanceBase,
    RemittanceLineSource,
    RemittanceStatus,
    SettlementStatus,
    TimeSegmentBase,
    TimeSegmentState,
    WorkLogBase,
)


class WorkLogPublic(WorkLogBase):
    id: uuid.UUID
    created_at: datetime


class WorkLogAmount(SQLModel):
    worklog_id: uuid.UUID
    remitted_amount_cents: int
    unremitted_amount_cents: int

    @computed_field  # type: ignore[misc]
    @property
    def total_amount_cents(self) -> int:
        return self.remitted_amount_cents + self.unremitted_amount_cents


class WorkLogWithAmount(SQLModel):
    worklog: WorkLogPublic
    amounts: WorkLogAmount


class WorkLogsPublic(SQLModel):
    data: list[WorkLogWithAmount]
    count: int


class TimeSegmentCreate(SQLModel):
    worklog_id: uuid.UUID
    started_at: datetime
    ended_at: datetime
    minutes: int
    hourly_rate_cents: int | None = None


class TimeSegmentPublic(TimeSegmentBase):
    id: uuid.UUID


class AdjustmentCreate(SQLModel):
    worklog_id: uuid.UUID
    amount_cents: int
    reason: str | None = None
    adjustment_type: AdjustmentType = AdjustmentType.CREDIT


class AdjustmentPublic(AdjustmentBase):
    id: uuid.UUID


class RemittancePublic(RemittanceBase):
    id: uuid.UUID


class RemittanceLinePublic(SQLModel):
    id: uuid.UUID
    remittance_id: uuid.UUID
    worklog_id: uuid.UUID
    source_id: uuid.UUID
    source_type: RemittanceLineSource
    amount_cents: int
    created_at: datetime


class RemittancesPublic(SQLModel):
    data: list[RemittancePublic]
    count: int


class RemittanceRunRequest(SQLModel):
    period_start: date | None = None
    period_end: date | None = None
    payout_status: RemittanceStatus | None = None
    dry_run: bool = False


class RemittanceRunResult(SQLModel):
    remittances: list[RemittancePublic]
    attempted_user_ids: list[uuid.UUID]
    dry_run: bool
