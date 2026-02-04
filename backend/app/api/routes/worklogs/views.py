import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.worklogs.service import WorkLogService, TimeEntryService, PaymentService
from app.models import (
    WorkLogCreate,
    WorkLogPublic,
    WorkLogsPublic,
    WorkLogUpdate,
    TimeEntryCreate,
    TimeEntryPublic,
    TimeEntriesPublic,
    TimeEntryUpdate,
    PaymentCreate,
    PaymentPublic,
    PaymentsPublic,
    Message,
)

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/", response_model=WorkLogsPublic)
def read_worklogs(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve worklogs.
    """
    return WorkLogService.get_worklogs(session, current_user, skip, limit)


@router.get("/{id}")
def read_worklog(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get worklog by ID with time entries.
    """
    return WorkLogService.get_worklog(session, current_user, id)


@router.post("/", response_model=WorkLogPublic, status_code=201)
def create_worklog(
    *, session: SessionDep, current_user: CurrentUser, worklog_in: WorkLogCreate
) -> Any:
    """
    Create new worklog.
    """
    return WorkLogService.create_worklog(session, current_user, worklog_in)


@router.put("/{id}", response_model=WorkLogPublic)
def update_worklog(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    worklog_in: WorkLogUpdate,
) -> Any:
    """
    Update a worklog.
    """
    return WorkLogService.update_worklog(session, current_user, id, worklog_in)


@router.delete("/{id}")
def delete_worklog(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a worklog.
    """
    return WorkLogService.delete_worklog(session, current_user, id)


@router.get("/filter/by-date-range")
def get_worklogs_by_date_range(
    session: SessionDep,
    current_user: CurrentUser,
    date_from: date,
    date_to: date,
) -> Any:
    """
    Get worklogs filtered by date range.
    """
    return WorkLogService.get_worklogs_by_date_range(session, current_user, date_from, date_to)


@router.post("/{id}/exclude", response_model=WorkLogPublic)
def exclude_worklog(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Exclude a worklog from payment.
    """
    return WorkLogService.exclude_worklog(session, current_user, id)


@router.get("/{worklog_id}/time-entries", response_model=TimeEntriesPublic)
def read_time_entries(
    session: SessionDep, current_user: CurrentUser, worklog_id: uuid.UUID
) -> Any:
    """
    Get time entries for a worklog.
    """
    return TimeEntryService.get_time_entries(session, current_user, worklog_id)


@router.post("/time-entries", response_model=TimeEntryPublic, status_code=201)
def create_time_entry(
    *, session: SessionDep, current_user: CurrentUser, time_entry_in: TimeEntryCreate
) -> Any:
    """
    Create new time entry.
    """
    return TimeEntryService.create_time_entry(session, current_user, time_entry_in)


@router.put("/time-entries/{id}", response_model=TimeEntryPublic)
def update_time_entry(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    time_entry_in: TimeEntryUpdate,
) -> Any:
    """
    Update a time entry.
    """
    return TimeEntryService.update_time_entry(session, current_user, id, time_entry_in)


@router.delete("/time-entries/{id}")
def delete_time_entry(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a time entry.
    """
    return TimeEntryService.delete_time_entry(session, current_user, id)


@router.get("/payments/", response_model=PaymentsPublic)
def read_payments(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve payments.
    """
    return PaymentService.get_payments(session, current_user, skip, limit)


@router.post("/payments/", status_code=201)
def create_payment(
    *, session: SessionDep, current_user: CurrentUser, payment_in: PaymentCreate
) -> Any:
    """
    Create new payment batch.
    """
    return PaymentService.create_payment(session, current_user, payment_in)


@router.post("/payments/{id}/confirm", response_model=PaymentPublic)
def confirm_payment(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Confirm payment and mark worklogs as PAID.
    """
    return PaymentService.confirm_payment(session, current_user, id)
