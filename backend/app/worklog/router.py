from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.worklog import schemas as worklog_schemas
from app.worklog import service as worklog_service

router = APIRouter(tags=["worklog"])


@router.post("/generate-remittances-for-all-users", response_model=worklog_schemas.GenerateRemittancesResponse)
def generate_remittances_for_all_users(session: SessionDep) -> Any:
    return worklog_service.WorkLogService.gen_rmtncs_for_all_usr(session)


@router.get("/list-all-worklogs", response_model=worklog_schemas.WorkLogsListResponse)
def list_all_worklogs(
    session: SessionDep,
    remittanceStatus: str | None = Query(None, description="Filter by remittance status: REMITTED or UNREMITTED"),
) -> Any:
    if remittanceStatus and remittanceStatus not in ["REMITTED", "UNREMITTED"]:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="remittanceStatus must be REMITTED or UNREMITTED")

    wls_with_amt = worklog_service.WorkLogService.get_wls_by_rmt_status(session, remittanceStatus)
    wl_responses = [
        worklog_schemas.WorkLogResponse(
            id=wl.id,
            user_id=wl.user_id,
            task_id=wl.task_id,
            amount=amt,
            created_at=wl.created_at,
            updated_at=wl.updated_at,
        )
        for wl, amt in wls_with_amt
    ]

    return worklog_schemas.WorkLogsListResponse(data=wl_responses, count=len(wl_responses))

