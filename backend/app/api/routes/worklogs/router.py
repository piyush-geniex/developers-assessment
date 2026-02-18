import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Task, TimeEntry, User, Worklog
from app.api.routes.worklogs import schemas as worklog_schemas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/worklogs", tags=["worklogs"])


def _worklog_list_item(
    w: Worklog,
    task_name: str,
    freelancer_name: str,
) -> worklog_schemas.WorklogListItem:
    return worklog_schemas.WorklogListItem(
        id=w.id,
        task_id=w.task_id,
        task_name=task_name,
        freelancer_id=w.owner_id,
        freelancer_name=freelancer_name,
        amount_earned=w.amount_earned,
        status=w.status,
        created_at=w.created_at,
    )


@router.get("/", response_model=worklog_schemas.WorklogListResponse)
def list_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
) -> Any:
    try:
        stmt = select(Worklog)
        if date_from:
            try:
                if "T" in date_from:
                    dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                else:
                    dt_from = datetime.fromisoformat(date_from + "T00:00:00")
                stmt = stmt.where(Worklog.created_at >= dt_from)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from")
        if date_to:
            try:
                if "T" in date_to:
                    dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                else:
                    dt_to = datetime.fromisoformat(date_to + "T23:59:59.999999")
                stmt = stmt.where(Worklog.created_at <= dt_to)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to")
        worklogs = list(session.exec(stmt).all())
        if not worklogs:
            return worklog_schemas.WorklogListResponse(data=[], count=0)
        task_ids = [w.task_id for w in worklogs]
        owner_ids = [w.owner_id for w in worklogs]
        tasks = {t.id: t for t in session.exec(select(Task).where(Task.id.in_(task_ids))).all()}
        users = {u.id: u for u in session.exec(select(User).where(User.id.in_(owner_ids))).all()}
        items = [
            _worklog_list_item(
                w,
                tasks.get(w.task_id).name if tasks.get(w.task_id) else "",
                users.get(w.owner_id).full_name or users.get(w.owner_id).email if users.get(w.owner_id) else "",
            )
            for w in worklogs
        ]
        return worklog_schemas.WorklogListResponse(data=items, count=len(items))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("list_worklogs failed: %s", e)
        return worklog_schemas.WorklogListResponse(data=[], count=0)


@router.get("/{worklog_id}", response_model=worklog_schemas.WorklogDetailResponse)
def get_worklog(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_id: uuid.UUID,
) -> Any:
    try:
        worklog = session.get(Worklog, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="Worklog not found")
        task = session.get(Task, worklog.task_id)
        owner = session.get(User, worklog.owner_id)
        task_name = task.name if task else ""
        freelancer_name = (owner.full_name or owner.email) if owner else ""
        entries = list(session.exec(select(TimeEntry).where(TimeEntry.worklog_id == worklog_id)).all())
        return worklog_schemas.WorklogDetailResponse(
            id=worklog.id,
            task_id=worklog.task_id,
            task_name=task_name,
            freelancer_id=worklog.owner_id,
            freelancer_name=freelancer_name,
            amount_earned=worklog.amount_earned,
            status=worklog.status,
            created_at=worklog.created_at,
            time_entries=[
                worklog_schemas.TimeEntryOut(
                    id=e.id,
                    description=e.description,
                    hours=e.hours,
                    rate=e.rate,
                    amount=e.amount,
                    logged_at=e.logged_at,
                )
                for e in entries
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_worklog failed: %s", e)
        raise HTTPException(status_code=404, detail="Worklog not found")
