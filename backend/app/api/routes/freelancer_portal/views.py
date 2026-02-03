"""API endpoints for freelancer portal."""
import uuid
from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.api.freelancer_deps import CurrentFreelancer
from app.models import (
    FreelancerDashboardStats,
    FreelancerPaymentInfo,
    FreelancerTimeEntryCreate,
    FreelancerWorkLogCreate,
    FreelancerWorkLogUpdate,
    Message,
    TimeEntryPublic,
    TimeEntryUpdate,
    WorkLogDetail,
    WorkLogStatus,
    WorkLogsSummaryPublic,
)

from .service import FreelancerPortalService

router = APIRouter(prefix="/freelancer", tags=["freelancer-portal"])


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard/stats", response_model=FreelancerDashboardStats)
def get_dashboard_stats(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
) -> Any:
    """
    Get dashboard statistics for the current freelancer.

    Returns counts of worklogs by status, total hours logged,
    total earned amount, and pending payment amount.
    """
    return FreelancerPortalService.get_dashboard_stats(session, current_freelancer)


# ============================================================================
# WORKLOGS
# ============================================================================

@router.get("/worklogs", response_model=WorkLogsSummaryPublic)
def get_my_worklogs(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    status: list[WorkLogStatus] | None = Query(default=None),
) -> Any:
    """
    Get worklogs for the current freelancer.

    Returns a paginated list of worklogs with aggregated time and amount data.
    Can be filtered by status.
    """
    return FreelancerPortalService.get_my_worklogs(
        session, current_freelancer, skip, limit, status
    )


@router.get("/worklogs/{worklog_id}", response_model=WorkLogDetail)
def get_worklog_detail(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    worklog_id: uuid.UUID,
) -> Any:
    """
    Get detailed information about a specific worklog.

    Only accessible if the worklog belongs to the current freelancer.
    """
    return FreelancerPortalService.get_worklog_detail(
        session, current_freelancer, worklog_id
    )


@router.post("/worklogs", response_model=WorkLogDetail)
def create_worklog(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    data: FreelancerWorkLogCreate,
) -> Any:
    """
    Create a new worklog with time entries.

    The worklog is created with PENDING status.
    At least one time entry is required.
    """
    return FreelancerPortalService.create_worklog(session, current_freelancer, data)


@router.patch("/worklogs/{worklog_id}", response_model=WorkLogDetail)
def update_worklog(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    worklog_id: uuid.UUID,
    data: FreelancerWorkLogUpdate,
) -> Any:
    """
    Update a worklog's task description.

    Only PENDING worklogs can be edited.
    """
    return FreelancerPortalService.update_worklog(
        session, current_freelancer, worklog_id, data
    )


@router.delete("/worklogs/{worklog_id}", response_model=Message)
def delete_worklog(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    worklog_id: uuid.UUID,
) -> Any:
    """
    Delete a worklog and its time entries.

    Only PENDING worklogs can be deleted.
    """
    FreelancerPortalService.delete_worklog(session, current_freelancer, worklog_id)
    return Message(message="WorkLog deleted successfully")


# ============================================================================
# TIME ENTRIES
# ============================================================================

@router.post("/worklogs/{worklog_id}/time-entries", response_model=TimeEntryPublic)
def add_time_entry(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    worklog_id: uuid.UUID,
    data: FreelancerTimeEntryCreate,
) -> Any:
    """
    Add a new time entry to a worklog.

    Only PENDING worklogs can have new time entries added.
    """
    return FreelancerPortalService.add_time_entry(
        session, current_freelancer, worklog_id, data
    )


@router.patch("/time-entries/{entry_id}", response_model=TimeEntryPublic)
def update_time_entry(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    entry_id: uuid.UUID,
    data: TimeEntryUpdate,
) -> Any:
    """
    Update a time entry.

    Only time entries belonging to PENDING worklogs can be edited.
    """
    return FreelancerPortalService.update_time_entry(
        session, current_freelancer, entry_id, data
    )


@router.delete("/time-entries/{entry_id}", response_model=Message)
def delete_time_entry(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    entry_id: uuid.UUID,
) -> Any:
    """
    Delete a time entry.

    Only time entries belonging to PENDING worklogs can be deleted.
    Cannot delete the last time entry of a worklog.
    """
    FreelancerPortalService.delete_time_entry(session, current_freelancer, entry_id)
    return Message(message="Time entry deleted successfully")


# ============================================================================
# PAYMENTS
# ============================================================================

@router.get("/payments", response_model=list[FreelancerPaymentInfo])
def get_my_payments(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
) -> Any:
    """
    Get payment history for the current freelancer.

    Returns a list of payment batches that include the freelancer's worklogs,
    with the total amount paid to this freelancer in each batch.
    """
    return FreelancerPortalService.get_my_payments(session, current_freelancer)
