from datetime import date
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.worklogs import service as worklog_service
from app.models import (
    PaymentBatchCreate,
    PaymentBatchPublic,
    WorkLogDetailPublic,
    WorkLogsPublic,
)

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/", response_model=WorkLogsPublic)
def list_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """List worklogs with earnings per task. Filter by date range for payment eligibility."""
    return worklog_service.get_worklogs(
        session, current_user, start_date, end_date, skip, limit
    )


@router.post("/payment-batch", response_model=PaymentBatchPublic)
def create_payment_batch(
    session: SessionDep,
    current_user: CurrentUser,
    payload: PaymentBatchCreate,
):
    """Create payment batch from selected worklogs. Exclude worklogs on frontend before sending IDs."""
    return worklog_service.create_payment_batch(
        session, current_user, payload
    )


@router.get("/{worklog_id}", response_model=WorkLogDetailPublic)
def get_worklog(
    session: SessionDep, current_user: CurrentUser, worklog_id: UUID
):
    """Get worklog detail with individual time entries."""
    return worklog_service.get_worklog_detail(
        session, current_user, worklog_id
    )
