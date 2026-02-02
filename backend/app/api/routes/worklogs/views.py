from typing import Any, Literal, Optional
import uuid

from fastapi import APIRouter, Query

from datetime import date
from app.api.deps import SessionDep, CurrentUser
from app.api.routes.worklogs.service import WorkLogService
from app.models import (
    WorkLogPublic,
    RemittanceGenerationResponse,
    RemittancePublic,
    RemittanceLineItemPublic, User, WorkLog,
)

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.get("/list-all-worklogs", response_model=list[WorkLogPublic])
def list_all_worklogs(
        session: SessionDep,
        # current_user: CurrentUser,
        remittance_status: Optional[Literal["REMITTED", "UNREMITTED"]] = Query(None, description="Filter by REMITTED or UNREMITTED")
) -> Any:
    """
    List all worklogs with filtering and amount information.

    Query Parameters:
    - remittanceStatus: Filter by remittance status (REMITTED or UNREMITTED)
      - REMITTED: Shows worklogs that are fully or partially paid
      - UNREMITTED: Shows worklogs that have no payments yet
    """
    if remittance_status and remittance_status.upper() not in ["REMITTED", "UNREMITTED"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="remittanceStatus must be either REMITTED or UNREMITTED"
        )

    return WorkLogService.list_all_worklogs(session, remittance_status)


@router.post("/generate-remittances-for-all-users", response_model=RemittanceGenerationResponse)
def generate_remittances_for_all_users(
        session: SessionDep,
        # current_user: CurrentUser,
        settlement_period: Optional[date] = Query(None, description="Settlement period (e.g., '2024-01-01')")
) -> Any:
    """
    Generate remittances for all users based on eligible work.

    This endpoint:
    1. Finds all unpaid work for each user
    2. Calculates the total amount owed
    3. Creates a single Remittance (one payment per user)
    4. Creates RemittanceLineItems for each worklog included
    """
    remittances = WorkLogService.generate_remittances_for_all_users(session, settlement_period)

    # Enrich with user info and line items
    enriched_remittances = []
    for remittance in remittances:
        user = session.get(User, remittance.user_id)

        line_items_enriched = []
        for item in remittance.line_items:
            worklog = session.get(WorkLog, item.worklog_id)
            line_items_enriched.append(
                RemittanceLineItemPublic(
                    id=item.id,
                    worklog_id=item.worklog_id,
                    amount=item.amount,
                    description=item.description,
                    task_name=worklog.task_name
                )
            )

        enriched_remittances.append(
            RemittancePublic(
                id=remittance.id,
                user_id=remittance.user_id,
                user_name=user.full_name or user.email,
                total_amount=remittance.total_amount,
                status=remittance.status,
                created_at=remittance.created_at,
                updated_at=remittance.updated_at,
                settlement_period=remittance.settlement_period,
                line_items=line_items_enriched
            )
        )

    return RemittanceGenerationResponse(
        total_remittances_created=len(enriched_remittances),
        remittances=enriched_remittances
    )


@router.post("/seed-test-data")
def seed_test_data(session: SessionDep) -> Any:
    """
    **[TEST DATA SEEDING]**

    Populates the database with realistic test data for the WorkLog Settlement System.

    Creates:
    - Multiple worklogs with time segments
    - Various adjustments (bonuses and deductions)
    - Historical remittances (both paid and failed)
    - Different scenarios to test all features

    **Use this endpoint to quickly set up test data!**
    """

    return WorkLogService.seed_data_into_db(session=session)
