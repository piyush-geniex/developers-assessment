import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.worklogs.service import WorkLogService
from app.models import (
    Message,
    WorkLogCreate,
    WorkLogDetail,
    WorkLogPublic,
    WorkLogsPublic,
    WorkLogsSummaryPublic,
    WorkLogStatus,
    WorkLogUpdate,
)

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/", response_model=WorkLogsPublic)
def read_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    freelancer_id: uuid.UUID | None = None,
    status: WorkLogStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> Any:
    """
    Retrieve worklogs with optional filters.
    """
    return WorkLogService.get_worklogs(
        session, skip, limit, freelancer_id, status, date_from, date_to
    )


@router.get("/summary", response_model=WorkLogsSummaryPublic)
def read_worklogs_summary(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    freelancer_id: uuid.UUID | None = None,
    status: list[WorkLogStatus] | None = Query(default=None),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> Any:
    """
    Retrieve aggregated worklog summary with calculated totals.
    This is the main endpoint for the dashboard - all calculations done in DB.
    """
    return WorkLogService.get_worklogs_summary(
        session, skip, limit, freelancer_id, status, date_from, date_to
    )


@router.get("/{worklog_id}", response_model=WorkLogPublic)
def read_worklog(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_id: uuid.UUID,
) -> Any:
    """
    Get a worklog by ID.
    """
    return WorkLogService.get_worklog(session, worklog_id)


@router.get("/{worklog_id}/detail", response_model=WorkLogDetail)
def read_worklog_detail(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_id: uuid.UUID,
) -> Any:
    """
    Get detailed worklog with time entries and calculated totals.
    """
    return WorkLogService.get_worklog_detail(session, worklog_id)


@router.post("/", response_model=WorkLogPublic)
def create_worklog(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_in: WorkLogCreate,
) -> Any:
    """
    Create a new worklog.
    """
    return WorkLogService.create_worklog(session, worklog_in)


@router.patch("/{worklog_id}", response_model=WorkLogPublic)
def update_worklog(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_id: uuid.UUID,
    worklog_in: WorkLogUpdate,
) -> Any:
    """
    Update a worklog.
    """
    return WorkLogService.update_worklog(session, worklog_id, worklog_in)


@router.patch("/{worklog_id}/status", response_model=WorkLogPublic)
def update_worklog_status(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_id: uuid.UUID,
    status: WorkLogStatus,
) -> Any:
    """
    Update worklog status with state machine validation.
    """
    return WorkLogService.update_worklog_status(session, worklog_id, status)


@router.delete("/{worklog_id}")
def delete_worklog(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_id: uuid.UUID,
) -> Message:
    """
    Delete a worklog.
    """
    WorkLogService.delete_worklog(session, worklog_id)
    return Message(message="WorkLog deleted successfully")
