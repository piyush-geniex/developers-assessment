from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.api.deps import get_db
from app.api.routes.worklogs import service
from app.api.routes.worklogs.models import Remittance, WorkLog
from app.api.routes.worklogs.schemas import (
    RemittancesGenerateResponse,
    RemittanceResponse,
    WorkLogsListResponse,
    WorkLogResponse,
)
from app.models import User

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


@router.post("/generate-remittances-for-all-users", response_model=RemittancesGenerateResponse)
def generate_remittances_for_all_users(db: Session = Depends(get_db)):
    """
    Generate remittances for all users based on eligible work.
    Creates a remittance for each user with unsettled work.
    """
    # Get all users
    usrs = db.exec(select(User)).all()
    
    # Period is current month
    now = datetime.utcnow()
    prd_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prd_end = now
    
    rmts = []
    ttl_amt = 0.0
    
    for u in usrs:
        try:
            rmt = service.gen_rmtnc_for_usr(db, u.id, prd_start, prd_end)
            if rmt:
                rmts.append(rmt)
                ttl_amt += rmt.amount
        except Exception as e:
            # Log and continue with other users
            print(f"Failed to generate remittance for user {u.id}: {e}")
            continue
    
    return RemittancesGenerateResponse(
        data=[
            RemittanceResponse(
                id=r.id,
                user_id=r.user_id,
                amount=r.amount,
                period_start=r.period_start,
                period_end=r.period_end,
                status=r.status,
                created_at=r.created_at,
                completed_at=r.completed_at
            )
            for r in rmts
        ],
        count=len(rmts),
        total_amount=ttl_amt
    )


@router.get("/list-all-worklogs", response_model=WorkLogsListResponse)
def list_all_worklogs(
    remittanceStatus: Optional[str] = Query(None, description="Filter by REMITTED or UNREMITTED"),
    db: Session = Depends(get_db)
):
    """
    List all worklogs with filtering and amount information.
    
    Query Parameters:
    - remittanceStatus: Filter by remittance status (REMITTED or UNREMITTED)
    
    Response includes the amount per worklog.
    """
    # Validate remittanceStatus if provided
    rmt_status = None
    if remittanceStatus:
        rmt_status = remittanceStatus.strip().upper()
        if rmt_status not in ["REMITTED", "UNREMITTED"]:
            rmt_status = None
    
    wls_data = service.get_all_wls_with_filter(db, rmt_status)
    
    return WorkLogsListResponse(
        data=[
            WorkLogResponse(
                id=wl["id"],
                user_id=wl["user_id"],
                task_name=wl["task_name"],
                amount=wl["amount"],
                created_at=wl["created_at"],
                remittance_status=wl["remittance_status"]
            )
            for wl in wls_data
        ],
        count=len(wls_data)
    )
