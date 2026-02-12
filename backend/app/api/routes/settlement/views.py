from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.api.routes.settlement.schemas import RemittanceResponse, WorklogListResponse
from app.api.routes.settlement.service import SettlementService

router = APIRouter(prefix="/settlement", tags=["settlement"])


@router.post(
    "/generate-remittances-for-all-users",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RemittanceResponse,
)
def generate_remittances(session: SessionDep) -> Any:
    """
    Generate remittances for all users based on eligible work.
    Superuser only.
    """
    return SettlementService.generate_remittances(session)


@router.get("/list-all-worklogs", response_model=WorklogListResponse)
def list_all_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    remittanceStatus: str | None = None,
) -> Any:
    """
    List all worklogs with amount and remittance status.
    Superusers see all worklogs; normal users see only their own.
    """
    return SettlementService.list_worklogs(
        session,
        current_user.id,
        current_user.is_superuser,
        remittanceStatus,
    )
