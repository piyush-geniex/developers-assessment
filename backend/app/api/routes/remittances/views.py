from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep, get_current_active_superuser
from app.api.routes.remittances.service import RemittanceService
from app.models import SettlementStatus
from app.schemas.remittance import RemittanceRunRequest, RemittanceRunResult, WorkLogsPublic

router = APIRouter(prefix="/remittances", tags=["remittances"])


@router.post(
    "/generate-remittances-for-all-users",
    response_model=RemittanceRunResult,
    dependencies=[Depends(get_current_active_superuser)],
)
async def generate_remittances_for_all_users(
    *, session: SessionDep, body: RemittanceRunRequest | None = None
) -> RemittanceRunResult:
    request = body or RemittanceRunRequest()
    return await RemittanceService.generate_remittances_for_all_users(
        session=session, body=request
    )


@router.get(
    "/list-all-worklogs",
    response_model=WorkLogsPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
async def list_all_worklogs(
    *,
    session: SessionDep,
    remittance_status: SettlementStatus | None = Query(
        default=None, alias="remittanceStatus", description="Filter by remittance status"
    ),
) -> WorkLogsPublic:
    return await RemittanceService.list_all_worklogs(
        session=session, remittance_status=remittance_status
    )
