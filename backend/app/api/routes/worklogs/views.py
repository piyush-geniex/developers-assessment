from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, get_current_active_superuser
from app.api.routes.worklogs.service import WorklogsService
from app.models import (
    GenerateRemittancesRequest,
    GenerateRemittancesResponse,
    WorkLog,
    WorkLogAdjustment,
    WorkLogAdjustmentCreate,
    WorkLogCreate,
    WorkLogSegment,
    WorkLogSegmentCreate,
    WorkLogsPublic,
)

router = APIRouter(prefix="", tags=["worklogs"])


@router.post(
    "/worklogs",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=WorkLog,
)
def create_worklog(session: SessionDep, body: WorkLogCreate) -> WorkLog:
    """Create a new WorkLog for a user."""
    return WorklogsService.create_worklog(session, body)


@router.post(
    "/worklogs/segments",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=WorkLogSegment,
)
def create_worklog_segment(
    session: SessionDep, body: WorkLogSegmentCreate
) -> WorkLogSegment:
    """Create a new WorkLog segment."""
    return WorklogsService.create_worklog_segment(session, body)


@router.post(
    "/worklogs/adjustments",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=WorkLogAdjustment,
)
def create_worklog_adjustment(
    session: SessionDep, body: WorkLogAdjustmentCreate
) -> WorkLogAdjustment:
    """Create a new WorkLog adjustment."""
    return WorklogsService.create_worklog_adjustment(session, body)


@router.post(
    "/generate-remittances-for-all-users",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=GenerateRemittancesResponse,
)
def generate_remittances_for_all_users(
    session: SessionDep, body: GenerateRemittancesRequest
) -> GenerateRemittancesResponse:
    """Generate remittances for all users based on eligible work."""
    return WorklogsService.generate_remittances_for_all_users(session, body)


@router.get(
    "/list-all-worklogs",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=WorkLogsPublic,
)
def list_all_worklogs(
    session: SessionDep, remittanceStatus: str | None = None
) -> WorkLogsPublic:
    """List all worklogs with their current amount and remittance status."""
    return WorklogsService.list_all_worklogs(session, remittanceStatus)
