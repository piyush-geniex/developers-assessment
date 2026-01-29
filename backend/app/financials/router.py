import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import User
from app.financials.models import TaskStatus, TaskStatusState
from app.financials.schemas import GenerateRemittancesResponse
from app.financials.service import FinancialService

router = APIRouter()


@router.post("/generate-remittances-for-all-users")
def generate_remittances(
    *, session: SessionDep, background_tasks: BackgroundTasks, _current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Generates remittances for all users based on eligible work.
    Returns a task_id for polling.
    """
    # Create TaskStatus
    task_status = TaskStatus(task_type="SETTLEMENT_RUN")
    session.add(task_status)
    session.commit()
    session.refresh(task_status)

    # Run in background
    background_tasks.add_task(
        FinancialService.run_settlement_process, session, task_status.id
    )

    return {
        "task_id": task_status.id,
        "message": "Settlement process started in background",
    }


@router.get("/task-status/{task_id}")
def get_task_status(
    *, session: SessionDep, task_id: uuid.UUID, _current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Poll for the status of a background task.
    """
    task = session.get(TaskStatus, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/remittances/{remittance_id}/cancel")
def cancel_remittance(
    *, session: SessionDep, remittance_id: uuid.UUID, _current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Cancel (pause) a pending remittance.
    """
    remittance = FinancialService.cancel_remittance(session, remittance_id)
    session.commit()
    session.refresh(remittance)
    return remittance


@router.post("/remittances/{remittance_id}/approve")
def approve_remittance(
    *, session: SessionDep, remittance_id: uuid.UUID, _current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Approve a paused (AWAITING_APPROVAL) remittance.
    """
    remittance = FinancialService.approve_remittance(session, remittance_id, _current_user.id)
    session.commit()
    session.refresh(remittance)
    return remittance