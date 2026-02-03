import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.payments.service import PaymentService
from app.models import (
    PaymentBatchDetail,
    PaymentBatchesPublic,
    PaymentPreviewResponse,
    PaymentProcessRequest,
    PaymentProcessResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/batches", response_model=PaymentBatchesPublic)
def read_payment_batches(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve payment batch history.
    """
    return PaymentService.get_payment_batches(session, skip, limit)


@router.get("/batches/{batch_id}", response_model=PaymentBatchDetail)
def read_payment_batch(
    session: SessionDep,
    current_user: CurrentUser,
    batch_id: uuid.UUID,
) -> Any:
    """
    Get payment batch details.
    """
    return PaymentService.get_payment_batch(session, batch_id)


@router.post("/preview", response_model=PaymentPreviewResponse)
def preview_payment(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_ids: list[uuid.UUID],
) -> Any:
    """
    Preview payment for selected worklogs.
    Returns detailed breakdown with validation issues.
    """
    return PaymentService.preview_payment(session, worklog_ids)


@router.post("/process", response_model=PaymentProcessResponse)
def process_payment(
    session: SessionDep,
    current_user: CurrentUser,
    request: PaymentProcessRequest,
) -> Any:
    """
    Process payment for selected worklogs.
    Creates a payment batch and updates worklog statuses to PAID.
    """
    return PaymentService.process_payment(session, current_user, request)
