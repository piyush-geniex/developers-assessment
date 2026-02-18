import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import PaymentBatch, Worklog
from app.api.routes.worklogs import schemas as worklog_schemas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payment-batches", tags=["payment-batches"])


@router.post("/", response_model=worklog_schemas.PaymentBatchResponse, status_code=201)
def create_payment_batch(
    session: SessionDep,
    current_user: CurrentUser,
    payload: worklog_schemas.PaymentBatchCreate,
) -> Any:
    try:
        exclude_wl = set(payload.exclude_worklog_ids or [])
        exclude_fl = set(payload.exclude_freelancer_ids or [])
        worklog_ids = payload.worklog_ids or []
        if not worklog_ids:
            eligible = []
        else:
            stmt = select(Worklog).where(
                Worklog.id.in_(worklog_ids),
                Worklog.status != "paid",
                Worklog.payment_batch_id.is_(None),
            )
            all_wls = list(session.exec(stmt).all())
            eligible = []
            for w in all_wls:
                try:
                    if w.id not in exclude_wl and w.owner_id not in exclude_fl:
                        _ = w.amount_earned
                        eligible.append(w)
                except Exception as e:
                    logger.error("Failed to include worklog %s in batch: %s", w.id, e)
                    continue
        total = sum(w.amount_earned for w in eligible)
        batch = PaymentBatch(worklog_count=len(eligible), total_amount=total)
        session.add(batch)
        session.commit()
        session.refresh(batch)
        for w in eligible:
            w.payment_batch_id = batch.id
            w.status = "paid"
            session.add(w)
        session.commit()
        return worklog_schemas.PaymentBatchResponse(
            id=batch.id,
            worklog_count=batch.worklog_count,
            total_amount=batch.total_amount,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("create_payment_batch failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Payment batch creation failed",
        )
