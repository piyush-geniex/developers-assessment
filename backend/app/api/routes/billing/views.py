from fastapi import APIRouter, Depends, Query
from typing import Any
from sqlmodel import Session

from app.api.deps import get_db
from .service import (
    generate_remittances_for_all_users,
    list_worklogs_by_remittance_status,
)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/generate-remittances-for-all-users")
def generate_remittances(session: Session = Depends(get_db)) -> Any:
    remittances = generate_remittances_for_all_users(session)

    if not remittances:
        return {"message": "No eligible work found for remittance."}

    return {
        "message": f"Generated {len(remittances)} remittances.",
        "remittances": [r.id for r in remittances],
    }


@router.get("/list-all-worklogs")
def list_worklogs(
    remittanceStatus: str = Query(..., pattern="^(REMITTED|UNREMITTED)$"),
    session: Session = Depends(get_db),
) -> Any:
    return list_worklogs_by_remittance_status(session, remittanceStatus)
