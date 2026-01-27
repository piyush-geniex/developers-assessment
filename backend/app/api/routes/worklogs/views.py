from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
	SessionDep,
	get_current_active_superuser,
)
from app.api.routes.worklogs.service import (
	SettlementService,
	WorkLogRemittanceStatus,
)

router = APIRouter(prefix="", tags=["worklogs"])


@router.get("/list-all-worklogs")
def list_all_worklogs(
	session: SessionDep,
	remittance_status: str | None = Query(
		default=None,
		alias="remittanceStatus",
		description="Filter by remittance status: REMITTED or UNREMITTED",
	),
) -> Any:
	if remittance_status is not None and remittance_status not in (
		WorkLogRemittanceStatus.REMITTED,
		WorkLogRemittanceStatus.UNREMITTED,
	):
		# Fast path validation without custom Pydantic enums
		from fastapi import HTTPException

		raise HTTPException(status_code=400, detail="Invalid remittanceStatus value")

	return SettlementService.list_all_worklogs(session, remittance_status)


@router.post(
	"/generate-remittances-for-all-users",
	dependencies=[Depends(get_current_active_superuser)],
)
def generate_remittances_for_all_users(
	session: SessionDep,
	period_start: date | None = Query(
		default=None,
		description="Optional settlement period start date (inclusive)",
	),
	period_end: date | None = Query(
		default=None,
		description="Optional settlement period end date (inclusive)",
	),
) -> Any:
	return SettlementService.generate_remittances_for_all_users(
		session=session,
		period_start=period_start,
		period_end=period_end,
	)
