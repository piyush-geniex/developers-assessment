from typing import Any

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.api.routes.worklogs.service import WorkLogService
from app.models import (
    PaymentBatchRequest,
    PaymentBatchResponse,
    WorkLogCreate,
    WorkLogPublic,
    WorkLogsPublic,
    WorkLogUpdate,
)

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/", response_model=WorkLogsPublic)
def read_worklogs(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Any:
    """
    Retrieve worklogs.
    """
    return WorkLogService.get_worklogs(session, skip, limit, start_date, end_date)


@router.get("/{wl_id}", response_model=WorkLogPublic)
def read_worklog(session: SessionDep, wl_id: int) -> Any:
    """
    Get worklog by ID.
    """
    return WorkLogService.get_worklog(session, wl_id)


@router.post("/", response_model=WorkLogPublic, status_code=201)
def create_worklog(*, session: SessionDep, wl_in: WorkLogCreate) -> Any:
    """
    Create new worklog.
    """
    return WorkLogService.create_worklog(session, wl_in)


@router.put("/{wl_id}", response_model=WorkLogPublic)
def update_worklog(*, session: SessionDep, wl_id: int, wl_in: WorkLogUpdate) -> Any:
    """
    Update a worklog.
    """
    return WorkLogService.update_worklog(session, wl_id, wl_in)


@router.delete("/{wl_id}")
def delete_worklog(session: SessionDep, wl_id: int) -> dict:
    """
    Delete a worklog.
    """
    return WorkLogService.delete_worklog(session, wl_id)


@router.post("/payment-batch", response_model=PaymentBatchResponse)
def process_payment_batch(*, session: SessionDep, req: PaymentBatchRequest) -> Any:
    """
    Process payment for selected worklogs.
    """
    return WorkLogService.process_payment_batch(session, req.worklog_ids)
