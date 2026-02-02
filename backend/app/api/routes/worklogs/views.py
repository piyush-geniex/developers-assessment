import uuid
from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.worklogs.service import WorkLogService
from app.models import (
    WorkLogDetail,
    WorkLogsPublic,
    WorkLogRemittanceFilter,
)

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/", response_model=WorkLogsPublic)
def list_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = Query(100, le=500),
    date_from: str | None = Query(None, description="Filter by time entry date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Filter by time entry date (YYYY-MM-DD)"),
    remittance_status: WorkLogRemittanceFilter | None = Query(
        None, description="REMITTED or UNREMITTED"
    ),
) -> Any:
    """
    List all worklogs with optional date range and remittance status filter.
    Returns amount earned per worklog.
    """
    return WorkLogService.list_worklogs(
        session,
        current_user,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        remittance_status=remittance_status,
    )


@router.get("/{work_log_id}", response_model=WorkLogDetail)
def get_worklog(
    session: SessionDep,
    current_user: CurrentUser,
    work_log_id: uuid.UUID,
) -> Any:
    """
    Get a worklog by ID with its time entries.
    """
    return WorkLogService.get_worklog(session, current_user, work_log_id)
