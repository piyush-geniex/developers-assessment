import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import User
from app.tasks.models import RemittanceStatus, Task, TimeSegment, WorkLog
from app.tasks.schemas import (
    DisputeCreate,
    DisputePublic,
    TaskCreate,
    TaskPublic,
    TasksPublic,
    TaskUpdate,
    TimeSegmentCreate,
    TimeSegmentPublic,
    TimeSegmentUpdate,
    WorkLogCreate,
    WorkLogPublic,
    WorkLogsPublic,
)
from app.tasks.service import TaskService

router = APIRouter()


# Tasks Endpoints
@router.post("/tasks", response_model=TaskPublic)
def create_task(
    *,
    session: SessionDep,
    _current_user: User = Depends(get_current_active_superuser),
    task_in: TaskCreate,
) -> Any:
    task = TaskService.create_task(session, task_in, _current_user.id)
    session.commit()
    session.refresh(task)
    return task


@router.get("/tasks/{task_id}", response_model=TaskPublic)
def get_task(
    *, session: SessionDep, _current_user: User = Depends(get_current_active_superuser), task_id: uuid.UUID
) -> Any:
    return TaskService.get_task(session, task_id)


@router.get("/tasks", response_model=TasksPublic)
def list_tasks(
    *, session: SessionDep, _current_user: User = Depends(get_current_active_superuser), skip: int = 0, limit: int = 100
) -> Any:
    return TaskService.get_tasks(session, skip, limit)


@router.put("/tasks/{task_id}", response_model=TaskPublic)
def update_task(
    *,
    session: SessionDep,
    _current_user: User = Depends(get_current_active_superuser),
    task_id: uuid.UUID,
    task_in: TaskUpdate,
) -> Any:
    task = TaskService.update_task(session, task_id, task_in)
    session.commit()
    session.refresh(task)
    return task


# WorkLogs Endpoints
@router.post("/worklogs", response_model=WorkLogPublic)
def create_worklog(
    *, session: SessionDep, _current_user: CurrentUser, worklog_in: WorkLogCreate
) -> Any:
    worklog = TaskService.create_worklog(session, worklog_in)
    session.commit()
    session.refresh(worklog)
    return worklog


@router.get("/worklogs/{worklog_id}", response_model=WorkLogPublic)
def get_worklog(
    *, session: SessionDep, _current_user: CurrentUser, worklog_id: uuid.UUID
) -> Any:
    return TaskService.get_worklog(session, worklog_id)


@router.get("/worklogs", response_model=WorkLogsPublic)
def list_worklogs(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    remittanceStatus: RemittanceStatus | None = None,
) -> Any:
    return TaskService.get_worklogs(session, skip, limit, remittanceStatus)


@router.get("/list-all-worklogs")
def list_all_worklogs_public(
    *,
    session: SessionDep,
    remittanceStatus: RemittanceStatus | None = Query(None),
    includeAccrued: bool = Query(False),
) -> Any:
    """
    Public endpoint to list all worklogs with filtering and amount information.
    """
    return TaskService.get_all_worklogs_with_amounts(
        session, remittanceStatus, includeAccrued
    )


# TimeSegments Endpoints
@router.post("/timesegments", response_model=TimeSegmentPublic)
def create_timesegment(
    *, session: SessionDep, _current_user: CurrentUser, segment_in: TimeSegmentCreate
) -> Any:
    segment = TaskService.create_timesegment(session, segment_in)
    session.commit()
    session.refresh(segment)
    return segment


@router.get("/timesegments/{segment_id}", response_model=TimeSegmentPublic)
def get_timesegment(
    *, session: SessionDep, _current_user: CurrentUser, segment_id: uuid.UUID
) -> Any:
    return TaskService.get_timesegment(session, segment_id)


@router.put("/timesegments/{segment_id}", response_model=TimeSegmentPublic)
def update_timesegment(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    segment_id: uuid.UUID,
    segment_in: TimeSegmentUpdate,
) -> Any:
    segment = TaskService.update_timesegment(session, segment_id, segment_in)
    session.commit()
    session.refresh(segment)
    return segment


@router.put("/timesegments/{segment_id}/dispute", response_model=DisputePublic)
def dispute_timesegment(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    segment_id: uuid.UUID,
    dispute_in: DisputeCreate,
) -> Any:
    dispute = TaskService.dispute_timesegment(session, segment_id, dispute_in.reason)
    session.commit()
    session.refresh(dispute)
    return dispute