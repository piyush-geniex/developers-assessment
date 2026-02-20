import uuid
from typing import Any
from datetime import datetime

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.work_logs.service import WorkLogService
from app.models import (
    WorkLogEntryCreate,
    WorkLogEntryItem,
    WorkLogEntries,
    WorkLogEntryUpdate,
    Message,
)

# This router is for nested routes under /tasks/{task_id}/work-logs
router = APIRouter(prefix="/{task_id}/work-logs", tags=["work-logs"])


@router.get("/", response_model=WorkLogEntries)
def read_work_logs(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> Any:
    """
    Retrieve work log entries for a task.
    """
    return WorkLogService.get_work_logs(
        session, current_user, task_id, skip, limit, start_time, end_time
    )


@router.get("/{work_log_id}", response_model=WorkLogEntryItem)
def read_work_log(
    session: SessionDep, current_user: CurrentUser, task_id: uuid.UUID, work_log_id: uuid.UUID
) -> Any:
    """
    Get work log entry by ID.
    """
    return WorkLogService.get_work_log(session, current_user, task_id, work_log_id)


@router.post("/", response_model=WorkLogEntryItem)
def create_work_log(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    work_log_in: WorkLogEntryCreate,
) -> Any:
    """
    Create new work log entry.
    """
    return WorkLogService.create_work_log(session, current_user, task_id, work_log_in)


@router.put("/{work_log_id}", response_model=WorkLogEntryItem)
def update_work_log(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    work_log_id: uuid.UUID,
    work_log_in: WorkLogEntryUpdate,
) -> Any:
    """
    Update a work log entry.
    """
    return WorkLogService.update_work_log(
        session, current_user, task_id, work_log_id, work_log_in
    )


@router.post("/{work_log_id}/approve", response_model=WorkLogEntryItem)
def approve_work_log(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    work_log_id: uuid.UUID,
) -> Any:
    """
    Approve a work log entry.
    """
    return WorkLogService.approve_work_log(session, current_user, task_id, work_log_id)


@router.post("/{work_log_id}/initiate-payment", response_model=WorkLogEntryItem)
def initiate_payment(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    work_log_id: uuid.UUID,
) -> Any:
    """
    Initiate payment for a work log entry.
    """
    return WorkLogService.initiate_payment(session, current_user, task_id, work_log_id)


@router.delete("/{work_log_id}")
def delete_work_log(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    work_log_id: uuid.UUID,
) -> Message:
    """
    Delete a work log entry.
    """
    return WorkLogService.delete_work_log(session, current_user, task_id, work_log_id)
