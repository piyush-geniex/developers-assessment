import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.tasks.service import TaskService
from app.models import Message, TaskCreate, TaskPublic, TasksPublic, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=TasksPublic)
def read_tasks(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    return TaskService.get_tasks(session, skip, limit)


@router.get("/{id}", response_model=TaskPublic)
def read_task(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    return TaskService.get_task(session, id)


@router.post("/", response_model=TaskPublic)
def create_task(*, session: SessionDep, current_user: CurrentUser, task_in: TaskCreate) -> Any:
    return TaskService.create_task(session, task_in)


@router.put("/{id}", response_model=TaskPublic)
def update_task(*, session: SessionDep, current_user: CurrentUser, id: uuid.UUID, task_in: TaskUpdate) -> Any:
    return TaskService.update_task(session, id, task_in)


@router.delete("/{id}")
def delete_task(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Message:
    return TaskService.delete_task(session, id)
