import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.worklogs.service import WorkLogService
from app.models import (
    PaymentBatchCreate,
    PaymentBatchDetail,
    PaymentBatchPublic,
    TaskCreate,
    TaskPublic,
    TimeEntryCreate,
    TimeEntryPublic,
    UserPublic,
    WorkLogCreate,
    WorkLogDetail,
    WorkLogPublic,
    WorkLogsPublic,
)

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/", response_model=WorkLogsPublic)
def read_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
) -> Any:
    """
    Retrieve worklogs with earnings.
    """
    return WorkLogService.get_worklogs(
        session, current_user, skip, limit, start_date, end_date
    )


@router.get("/tasks", response_model=list[TaskPublic])
def get_tasks(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Get all tasks.
    """
    return WorkLogService.get_tasks(session, skip, limit)


@router.get("/freelancers", response_model=list[UserPublic])
def get_freelancers(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Get all freelancers (users).
    """
    return WorkLogService.get_freelancers(session, skip, limit)


@router.get("/{id}", response_model=WorkLogDetail)
def read_worklog(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get worklog by ID with time entries.
    """
    return WorkLogService.get_worklog(session, current_user, id)


@router.post("/payment-batch", response_model=PaymentBatchDetail)
def create_payment_batch(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    batch_in: PaymentBatchCreate,
) -> Any:
    """
    Create payment batch with date range and exclusions.
    """
    return WorkLogService.create_payment_batch(session, current_user, batch_in)


@router.post("/payment-batch/{id}/confirm", response_model=PaymentBatchPublic)
def confirm_payment_batch(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Confirm and process payment batch.
    """
    return WorkLogService.confirm_payment_batch(session, current_user, id)


@router.delete(
    "/payment-batch/{batch_id}/payments/{payment_id}", response_model=dict[str, str]
)
def delete_payment_from_batch(
    session: SessionDep,
    current_user: CurrentUser,
    batch_id: uuid.UUID,
    payment_id: uuid.UUID,
) -> Any:
    """
    Delete a payment from a payment batch.
    """
    return WorkLogService.delete_payment_from_batch(
        session, current_user, batch_id, payment_id
    )


@router.post("/tasks", response_model=TaskPublic)
def create_task(
    *, session: SessionDep, current_user: CurrentUser, task_in: TaskCreate
) -> Any:
    """
    Create a new task.
    """
    return WorkLogService.create_task(session, current_user, task_in)


@router.post("/", response_model=WorkLogPublic)
def create_worklog(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    worklog_in: WorkLogCreate,
) -> Any:
    """
    Create a new worklog.
    """
    return WorkLogService.create_worklog(session, current_user, worklog_in)


@router.post("/time-entries", response_model=TimeEntryPublic)
def create_time_entry(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    time_entry_in: TimeEntryCreate,
) -> Any:
    """
    Create a new time entry.
    """
    return WorkLogService.create_time_entry(session, current_user, time_entry_in)

