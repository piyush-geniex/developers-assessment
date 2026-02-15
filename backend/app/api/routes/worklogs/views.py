from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query

from app.api.deps import SessionDep
from app.api.routes.worklogs.service import WorklogsService
from app.models import (
    GenerateRemittancesForAllUsersRequest,
    GenerateRemittancesForAllUsersResponse,
    WorklogRemittanceStatus,
    WorklogsAmountsPublic,
)

router = APIRouter(tags=["worklogs"])


@router.post(
    "/generate-remittances-for-all-users",
    response_model=GenerateRemittancesForAllUsersResponse,
)
def generate_remittances_for_all_users(
    session: SessionDep,
    body: GenerateRemittancesForAllUsersRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    payout_mode: str | None = Header(default=None, alias="X-Payout-Mode"),
) -> Any:
    if payout_mode and payout_mode not in ("success", "fail", "cancel"):
        raise HTTPException(status_code=400, detail="Invalid X-Payout-Mode value")
    return WorklogsService.generate_remittances_for_all_users(
        session=session,
        payload=body,
        idempotency_key_header=idempotency_key,
        payout_mode=payout_mode,
    )


@router.get("/list-all-worklogs", response_model=WorklogsAmountsPublic)
def list_all_worklogs(
    session: SessionDep,
    remittance_status: str | None = Query(default=None, alias="remittanceStatus"),
) -> Any:
    if remittance_status and remittance_status not in (
        WorklogRemittanceStatus.REMITTED,
        WorklogRemittanceStatus.UNREMITTED,
    ):
        raise HTTPException(status_code=400, detail="Invalid remittanceStatus filter")
    return WorklogsService.list_all_worklogs(
        session=session, remittance_status=remittance_status
    )
