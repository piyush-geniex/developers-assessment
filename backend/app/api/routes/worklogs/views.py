from cgitb import reset
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.worklogs.schemas import (
    FreelancerCreateRequest,
    PaymentBatchRequest,
    TimeSegmentCreateRequest,
    WorkLogCreateRequest,
    WorkLogDetail,
    WorkLogWithEarnings,
)
from app.api.routes.worklogs.service import WorkLogService
from app.models import (
    Freelancer,
    FreelancerCreate,
    FreelancerPublic,
    FreelancersPublic,
    FreelancerUpdate,
    Item,
    Message,
    TimeSegment,
    TimeSegmentCreate,
    TimeSegmentPublic,
    TimeSegmentsPublic,
    TimeSegmentUpdate,
    WorkLog,
    WorkLogCreate,
    WorkLogPublic,
    WorkLogsPublic,
    WorkLogUpdate,
)

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


# Freelancer Management
@router.post("/freelancers", response_model=FreelancerPublic)
def create_freelancer(
    *, session: SessionDep, current_user: CurrentUser, req: FreelancerCreateRequest
) -> Any:
    """Create new freelancer"""
    fr_in = FreelancerCreate(
        full_name=req.full_name,
        hourly_rate=req.hourly_rate,
        status=req.status,
    )
    fr = Freelancer.model_validate(fr_in)
    session.add(fr)
    session.commit()
    session.refresh(fr)
    return fr


@router.get("/freelancers", response_model=FreelancersPublic)
def list_freelancers(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """List all freelancers"""
    stmt = select(Freelancer).offset(skip).limit(limit)
    frs = session.exec(stmt).all()
    cnt = len(frs)
    return FreelancersPublic(data=frs, count=cnt)


@router.get("/freelancers/{id}", response_model=FreelancerPublic)
def get_freelancer(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """Get freelancer by ID"""
    fr = session.get(Freelancer, id)
    if not fr:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    return fr


@router.put("/freelancers/{id}", response_model=FreelancerPublic)
def update_freelancer(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    fr_in: FreelancerUpdate,
) -> Any:
    """Update freelancer"""
    fr = session.get(Freelancer, id)
    if not fr:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    upd = fr_in.model_dump(exclude_unset=True)
    fr.sqlmodel_update(upd)
    session.add(fr)
    session.commit()
    session.refresh(fr)
    return fr


@router.delete("/freelancers/{id}", response_model=FreelancerPublic)
def delete_freelancer(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """Delete freelancer"""
    fr = session.get(Freelancer, id)
    if not fr:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    session.delete(fr)
    session.commit()
    return Message(message="Freelancer deleted successfully")


# WorkLog CRUD
@router.post("/", response_model=WorkLogPublic)
def create_worklog(
    *, session: SessionDep, current_user: CurrentUser, req: WorkLogCreateRequest
) -> Any:
    """Create new worklog"""
    wl_in = WorkLogCreate(
        freelancer_id=req.freelancer_id,
        item_id=req.item_id,
        hours=req.hours,
    )
    wl = WorkLog.model_validate(wl_in)
    session.add(wl)
    session.commit()
    session.refresh(wl)
    
    # Fetch item_title from Item table
    itm = session.get(Item, wl.item_id)
    itm_title = itm.title if itm else ""
    
    return WorkLogPublic(
        id=wl.id,
        freelancer_id=wl.freelancer_id,
        item_id=wl.item_id,
        item_title=itm_title,
        hours=wl.hours,
        payment_status=wl.payment_status,
        created_at=wl.created_at,
        paid_at=wl.paid_at,
    )


@router.get("/", response_model=list[WorkLogWithEarnings])
def list_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 1000,
    payment_status: str | None = None,
) -> Any:
    """
    List worklogs with earnings
    wls: worklogs
    """
    stmt = select(WorkLog)
    if payment_status:
        stmt = stmt.where(WorkLog.payment_status == payment_status.upper())
    stmt = stmt.offset(skip).limit(limit)
    wls = session.exec(stmt).all()

    res = []
    for wl in wls:
        try:
            fr = session.get(Freelancer, wl.freelancer_id)
            if not fr:
                continue

            # Fetch item_title from Item table
            itm = session.get(Item, wl.item_id)
            itm_title = itm.title if itm else ""

            amt = wl.hours * fr.hourly_rate

            res.append(
                WorkLogWithEarnings(
                    id=wl.id,
                    item_id=wl.item_id,
                    item_title=itm_title,
                    hours=wl.hours,
                    payment_status=wl.payment_status,
                    freelancer_id=wl.freelancer_id,
                    freelancer_name=fr.full_name,
                    created_at=wl.created_at,
                    paid_at=wl.paid_at,
                    amount_earned=amt,
                )
            )
        except Exception:
            continue

    return res


@router.get("/{id}", response_model=WorkLogDetail)
def get_worklog(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get worklog with time segments
    wl: worklog
    segs: time segments
    """
    wl = session.get(WorkLog, id)
    if not wl:
        raise HTTPException(status_code=404, detail="WorkLog not found")

    fr = session.get(Freelancer, wl.freelancer_id)
    if not fr:
        raise HTTPException(status_code=404, detail="Freelancer not found")

    # Fetch item_title from Item table
    itm = session.get(Item, wl.item_id)
    itm_title = itm.title if itm else ""

    segs = session.exec(select(TimeSegment).where(TimeSegment.worklog_id == id)).all()

    seg_list = []
    for s in segs:
        seg_list.append(
            {
                "id": str(s.id),
                "hours": s.hours,
                "segment_date": s.segment_date.isoformat(),
                "notes": s.notes,
            }
        )

    amt = wl.hours * fr.hourly_rate

    return WorkLogDetail(
        id=wl.id,
        item_id=wl.item_id,
        item_title=itm_title,
        hours=wl.hours,
        payment_status=wl.payment_status,
        freelancer_id=wl.freelancer_id,
        freelancer_name=fr.full_name,
        hourly_rate=fr.hourly_rate,
        created_at=wl.created_at,
        paid_at=wl.paid_at,
        time_segments=seg_list,
        amount_earned=amt,
    )


@router.put("/{id}", response_model=WorkLogPublic)
def update_worklog(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    wl_in: WorkLogUpdate,
) -> Any:
    """Update worklog"""
    wl = session.get(WorkLog, id)
    if not wl:
        raise HTTPException(status_code=404, detail="WorkLog not found")
    upd = wl_in.model_dump(exclude_unset=True)
    wl.sqlmodel_update(upd)
    session.add(wl)
    session.commit()
    session.refresh(wl)
    
    # Fetch item_title from Item table
    itm = session.get(Item, wl.item_id)
    itm_title = itm.title if itm else ""
    
    return WorkLogPublic(
        id=wl.id,
        freelancer_id=wl.freelancer_id,
        item_id=wl.item_id,
        item_title=itm_title,
        hours=wl.hours,
        payment_status=wl.payment_status,
        created_at=wl.created_at,
        paid_at=wl.paid_at,
    )


@router.delete("/{id}", response_model=WorkLogPublic)
def delete_worklog(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """Delete worklog"""
    wl = session.get(WorkLog, id)
    if not wl:
        raise HTTPException(status_code=404, detail="WorkLog not found")
    session.delete(wl)
    session.commit()
    return Message(message="WorkLog deleted successfully")


# TimeSegment Operations
@router.post("/{id}/segments", response_model=TimeSegmentPublic)
def add_time_segment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    req: TimeSegmentCreateRequest,
) -> Any:
    """
    Add time segment to worklog
    seg: time segment
    """
    wl = session.get(WorkLog, id)
    if not wl:
        raise HTTPException(status_code=404, detail="WorkLog not found")

    seg_in = TimeSegmentCreate(
        worklog_id=id,
        hours=req.hours,
        segment_date=req.segment_date,
        notes=req.notes,
    )
    seg = TimeSegment.model_validate(seg_in)
    session.add(seg)
    session.commit()
    session.refresh(seg)
    return seg


@router.put("/{id}/segments/{seg_id}", response_model=TimeSegmentPublic)
def update_time_segment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    seg_id: uuid.UUID,
    seg_in: TimeSegmentUpdate,
) -> Any:
    """Update time segment"""
    seg = session.get(TimeSegment, seg_id)
    if not seg:
        raise HTTPException(status_code=404, detail="TimeSegment not found")
    if seg.worklog_id != id:
        raise HTTPException(status_code=400, detail="Segment does not belong to worklog")
    upd = seg_in.model_dump(exclude_unset=True)
    seg.sqlmodel_update(upd)
    session.add(seg)
    session.commit()
    session.refresh(seg)
    return seg


@router.delete("/{id}/segments/{seg_id}")
def delete_time_segment(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID, seg_id: uuid.UUID
) -> Message:
    """Delete time segment"""
    seg = session.get(TimeSegment, seg_id)
    if not seg:
        raise HTTPException(status_code=404, detail="TimeSegment not found")
    if seg.worklog_id != id:
        raise HTTPException(status_code=400, detail="Segment does not belong to worklog")
    session.delete(seg)
    session.commit()
    return Message(message="TimeSegment deleted successfully")


# Payment Processing
@router.get("/payment-eligible/list", response_model=list[WorkLogWithEarnings])
def get_payment_eligible_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Any:
    """
    Get worklogs eligible for payment
    wls: worklogs
    """
    stmt = select(WorkLog).where(WorkLog.payment_status == "UNPAID")

    if start_date:
        sd = datetime.fromisoformat(start_date)
        stmt = stmt.where(WorkLog.created_at >= sd)

    if end_date:
        ed = datetime.fromisoformat(end_date)
        stmt = stmt.where(WorkLog.created_at <= ed)

    wls = session.exec(stmt).all()

    res = []
    for wl in wls:
        try:
            fr = session.get(Freelancer, wl.freelancer_id)
            if not fr:
                continue

            # Fetch item_title from Item table
            itm = session.get(Item, wl.item_id)
            itm_title = itm.title if itm else ""

            amt = wl.hours * fr.hourly_rate

            res.append(
                WorkLogWithEarnings(
                    id=wl.id,
                    item_id=wl.item_id,
                    item_title=itm_title,
                    hours=wl.hours,
                    payment_status=wl.payment_status,
                    freelancer_id=wl.freelancer_id,
                    freelancer_name=fr.full_name,
                    created_at=wl.created_at,
                    paid_at=wl.paid_at,
                    amount_earned=amt,
                )
            )
        except Exception:
            continue

    return res


@router.post("/process-payment")
def process_payment_batch(
    *, session: SessionDep, current_user: CurrentUser, req: PaymentBatchRequest
) -> Any:
    """
    Process payment batch
    wl_ids: worklog ids
    """
    result = WorkLogService.proc_pay_batch(session, req.worklog_ids)
    return result
