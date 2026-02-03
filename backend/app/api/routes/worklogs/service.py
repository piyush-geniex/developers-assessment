import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.api.routes.worklogs.models import (
    Adjustment,
    Remittance,
    TimeSegment,
    WorkLog,
    WorkLogSettlement,
)


def calc_wl_amt(db: Session, wl_id: uuid.UUID) -> float:
    """
    Calculate total amount for a worklog
    wl_id: worklog id
    Returns: total amount (segments - adjustments)
    """
    # Get all active time segments
    segs = db.exec(
        select(TimeSegment)
        .where(TimeSegment.worklog_id == wl_id)
        .where(TimeSegment.is_removed == False)
    ).all()
    
    seg_ttl = 0.0
    for s in segs:
        seg_ttl += s.hours * s.rate
    
    # Get all adjustments
    adjs = db.exec(
        select(Adjustment).where(Adjustment.worklog_id == wl_id)
    ).all()
    
    adj_ttl = 0.0
    for a in adjs:
        adj_ttl += a.amount
    
    return seg_ttl + adj_ttl


def calc_unsettled_amt(db: Session, wl_id: uuid.UUID) -> float:
    """
    Calculate unsettled amount for a worklog
    wl_id: worklog id
    Returns: amount not yet included in completed remittances
    """
    ttl_amt = calc_wl_amt(db, wl_id)
    
    # Get sum of amounts already settled in completed remittances
    stlmnts = db.exec(
        select(WorkLogSettlement)
        .where(WorkLogSettlement.worklog_id == wl_id)
    ).all()
    
    settled_amt = 0.0
    for s in stlmnts:
        # Check if remittance was completed
        rmt = db.exec(
            select(Remittance)
            .where(Remittance.id == s.remittance_id)
            .where(Remittance.status == "COMPLETED")
        ).first()
        
        if rmt:
            settled_amt += s.amount_settled
    
    return ttl_amt - settled_amt


def get_wl_rmt_status(db: Session, wl_id: uuid.UUID) -> str:
    """
    Get remittance status for a worklog
    wl_id: worklog id
    Returns: REMITTED or UNREMITTED
    """
    unsettled = calc_unsettled_amt(db, wl_id)
    
    # If there's any unsettled amount (positive or negative), it's unremitted
    if abs(unsettled) > 0.01:  # Small threshold for floating point
        return "UNREMITTED"
    
    # Check if there are any completed settlements
    stlmnts = db.exec(
        select(WorkLogSettlement)
        .where(WorkLogSettlement.worklog_id == wl_id)
    ).all()
    
    for s in stlmnts:
        rmt = db.exec(
            select(Remittance)
            .where(Remittance.id == s.remittance_id)
            .where(Remittance.status == "COMPLETED")
        ).first()
        
        if rmt:
            return "REMITTED"
    
    return "UNREMITTED"


def gen_rmtnc_for_usr(db: Session, u_id: uuid.UUID, prd_start: datetime, prd_end: datetime) -> Optional[Remittance]:
    """
    Generate remittance for a user
    u_id: user id
    prd_start: period start
    prd_end: period end
    Returns: created remittance or None if no work to settle
    """
    # Get all worklogs for user
    wls = db.exec(
        select(WorkLog)
        .where(WorkLog.user_id == u_id)
    ).all()
    
    # Calculate total unsettled amount
    ttl = 0.0
    wl_amts = {}
    
    for wl in wls:
        unsettled = calc_unsettled_amt(db, wl.id)
        if abs(unsettled) > 0.01:  # Only include if there's meaningful amount
            wl_amts[wl.id] = unsettled
            ttl += unsettled
    
    # Don't create remittance if nothing to settle
    if abs(ttl) < 0.01:
        return None
    
    # Create remittance
    rmt = Remittance(
        user_id=u_id,
        amount=max(ttl, 0),  # Don't pay negative amounts
        period_start=prd_start,
        period_end=prd_end,
        status="COMPLETED",
        completed_at=datetime.utcnow()
    )
    db.add(rmt)
    db.commit()
    db.refresh(rmt)
    
    # Create settlements for each worklog
    for wl_id, amt in wl_amts.items():
        stlmnt = WorkLogSettlement(
            worklog_id=wl_id,
            remittance_id=rmt.id,
            amount_settled=amt
        )
        db.add(stlmnt)
    
    db.commit()
    
    return rmt


def get_all_wls_with_filter(db: Session, rmt_status: Optional[str] = None) -> list[dict]:
    """
    Get all worklogs with optional remittance status filter
    rmt_status: REMITTED or UNREMITTED or None
    Returns: list of worklog dicts with amount and status
    """
    wls = db.exec(select(WorkLog)).all()
    
    result = []
    for wl in wls:
        amt = calc_wl_amt(db, wl.id)
        status = get_wl_rmt_status(db, wl.id)
        
        # Apply filter if provided
        if rmt_status and status != rmt_status:
            continue
        
        result.append({
            "id": wl.id,
            "user_id": wl.user_id,
            "task_name": wl.task_name,
            "amount": amt,
            "created_at": wl.created_at,
            "remittance_status": status
        })
    
    return result
