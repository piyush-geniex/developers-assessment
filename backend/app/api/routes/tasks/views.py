import uuid
from typing import Any
from datetime import datetime

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.tasks.service import TaskService
from app.api.routes.work_logs import views as work_logs_views
from app.api.routes.work_logs.service import WorkLogService
from app.models import TaskCreate, TaskItem, TaskItems, TaskUpdate, Message, WorkLogEntries, WorkLogEntryBulkDelete, WorkLogEntryBulkPaymentInitiate

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Include work logs as nested routes under tasks
router.include_router(work_logs_views.router)


@router.get("/work-logs", response_model=WorkLogEntries)
def read_all_work_logs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> Any:
    """
    Retrieve all work log entries across all tasks.
    """
    return WorkLogService.get_all_work_logs(session, current_user, skip, limit, start_time, end_time)


@router.post("/work-logs/bulk-initiate-payment", response_model=Message)
def initiate_payments(
    session: SessionDep,
    current_user: CurrentUser,
    work_log_ids: WorkLogEntryBulkPaymentInitiate,
) -> Message:
    """
    Initiate payment for multiple work log entries.
    """
    return TaskService.initiate_payments(session, current_user, work_log_ids.entry_ids)


@router.delete("/work-logs/delete", response_model=Message)
def bulk_delete(
    session: SessionDep,
    work_log_ids: WorkLogEntryBulkDelete,
) -> Message:
    """
    Delete multiple work log entries.
    """
    return TaskService.bulk_delete_work_logs(session, work_log_ids.entry_ids)


@router.get("/", response_model=TaskItems)
def read_tasks(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> Any:
    """
    Retrieve tasks.
    
    Optional date filters:
    - start_date: Filter tasks created on or after this date
    - end_date: Filter tasks created on or before this date
    """
    return TaskService.get_tasks(session, current_user, skip, limit, start_date, end_date)


@router.get("/{task_id}", response_model=TaskItem)
def read_task(session: SessionDep, current_user: CurrentUser, task_id: uuid.UUID) -> Any:
    """
    Get task by ID.
    """
    return TaskService.get_task(session, current_user, task_id)


@router.post("/", response_model=TaskItem)
def create_task(
    *, session: SessionDep, current_user: CurrentUser, task_in: TaskCreate
) -> Any:
    """
    Create new task.
    """
    return TaskService.create_task(session, current_user, task_in)


@router.put("/{task_id}", response_model=TaskItem)
def update_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    task_in: TaskUpdate,
) -> Any:
    """
    Update a task.
    """
    return TaskService.update_task(session, current_user, task_id, task_in)


@router.delete("/{task_id}", response_model=Message)
def delete_task(
    session: SessionDep, current_user: CurrentUser, task_id: uuid.UUID
) -> Message:
    """
    Delete a task.
    """
    return TaskService.delete_task(session, current_user, task_id)
