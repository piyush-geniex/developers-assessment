from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import TimeEntry, UserRole, WorklogsSummary

from .service import WorklogService

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/summary", response_model=WorklogsSummary)
def read_worklogs_summary(
    session: SessionDep,
    current_user: CurrentUser,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    freelancer_id: str | None = Query(None),
) -> Any:
    is_admin = current_user.is_superuser or current_user.role == UserRole.ADMIN
    if not is_admin:
        freelancer_id = str(current_user.id)

    summaries = WorklogService.get_worklog_summary(
        session=session,
        date_from=date_from,
        date_to=date_to,
        freelancer_id=freelancer_id,
    )

    count_statement = select(func.count()).select_from(TimeEntry)
    if date_from:
        count_statement = count_statement.where(TimeEntry.start_time >= date_from)
    if date_to:
        count_statement = count_statement.where(TimeEntry.end_time <= date_to)
    if freelancer_id:
        count_statement = count_statement.where(TimeEntry.freelancer_id == freelancer_id)

    count = session.exec(count_statement).one()

    return WorklogsSummary(data=summaries, count=count)
