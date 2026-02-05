from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.api.routes.worklogs.service import WorklogService
from app.models import (
    TimeEntryCreate,
    TimeEntryPublic,
    PaymentBatchCreate,
    PaymentBatchPublic,
    WorklogCreate,
    WorklogDetail,
    WorklogsPublic,
)


router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.post("/", response_model=WorklogDetail, status_code=201)
def create_worklog(session: SessionDep, body: WorklogCreate) -> Any:
    wl = WorklogService.create_worklog(session, body)
    # Reuse detail builder so response has total and entries
    return WorklogService.get_worklog_detail(session, wl.id)


@router.post("/{worklog_id}/entries", response_model=TimeEntryPublic, status_code=201)
def create_time_entry(
    session: SessionDep, worklog_id: uuid.UUID, body: TimeEntryCreate
) -> Any:
    return WorklogService.create_time_entry(session, worklog_id, body)


@router.get("/", response_model=WorklogsPublic)
def read_worklogs(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    from_date: date | None = None,
    to_date: date | None = None,
    freelancer_id: uuid.UUID | None = None,
    status: str | None = None,
) -> Any:
    return WorklogService.list_worklogs(
        session=session,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        freelancer_id=freelancer_id,
        status=status,
    )


@router.get("/{worklog_id}", response_model=WorklogDetail)
def read_worklog(session: SessionDep, worklog_id: uuid.UUID) -> Any:
    return WorklogService.get_worklog_detail(session, worklog_id)


@router.post("/payment-preview", response_model=PaymentBatchPublic, status_code=200)
def payment_preview(session: SessionDep, body: PaymentBatchCreate) -> Any:
    return WorklogService.payment_preview(session, body)


@router.post("/payment-batch", response_model=PaymentBatchPublic, status_code=201)
def create_payment_batch(session: SessionDep, body: PaymentBatchCreate) -> Any:
    return WorklogService.create_payment_batch(session, body)
