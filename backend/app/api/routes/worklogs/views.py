import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.worklogs.service import WorklogService
from app.models import WorklogCreate, WorklogDetail, WorklogPublic, WorklogsPublic

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/", response_model=WorklogsPublic)
def read_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Any:
    """
    List worklogs with aggregated hours and earnings.
    Supports optional date range filtering by time entry start date.
    Superusers see all worklogs; other users see only their own.
    """
    return WorklogService.list_worklogs(
        session, current_user, skip, limit, date_from, date_to
    )


@router.get("/{worklog_id}", response_model=WorklogDetail)
def read_worklog(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_id: uuid.UUID,
) -> Any:
    """
    Get a worklog with all its time entries.
    """
    return WorklogService.get_worklog(session, current_user, worklog_id)


@router.post("/", response_model=WorklogPublic, status_code=201)
def create_worklog(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    worklog_in: WorklogCreate,
) -> Any:
    """
    Create a new worklog. The authenticated user becomes the freelancer owner.
    """
    return WorklogService.create_worklog(session, current_user, worklog_in)
