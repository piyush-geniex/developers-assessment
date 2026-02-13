import uuid
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.worklogs.service import WorkLogService
from app.models import (
    Message,
    PaymentBatchCreate,
    WorkLogDetail,
    WorkLogsPublic,
)

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/", response_model=WorkLogsPublic)
def read_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve worklogs with filters.
    """
    return WorkLogService.get_worklogs(session, start_date, end_date, skip, limit)


@router.get("/{id}", response_model=WorkLogDetail)
def read_worklog(
    session: SessionDep, 
    current_user: CurrentUser, 
    id: uuid.UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Any:
    """
    Get worklog by ID with details.
    """
    return WorkLogService.get_worklog(session, id, start_date, end_date)


@router.post("/process-payments", response_model=Message)
def process_payments(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    batch_in: PaymentBatchCreate,
) -> Any:
    """
    Process payments for a batch of worklogs.
    """
    if not current_user.is_superuser:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return WorkLogService.process_payments(
        session, batch_in.worklog_ids, batch_in.time_entry_ids, batch_in.excluded_freelancer_ids
    )
