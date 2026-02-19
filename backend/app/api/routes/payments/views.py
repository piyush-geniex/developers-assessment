import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.api.routes.payments.service import PaymentService
from app.models import (
    ConfirmBatchIn,
    Message,
    PaymentBatchCreate,
    PaymentBatchDetail,
    PaymentBatchPublic,
    PaymentBatchesPublic,
)

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    dependencies=[Depends(get_current_active_superuser)],
)


@router.get("/batches", response_model=PaymentBatchesPublic)
def read_batches(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    List all payment batches (admin only).
    """
    return PaymentService.list_batches(session, skip, limit)


@router.post("/batches", response_model=PaymentBatchDetail, status_code=201)
def create_batch(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    batch_in: PaymentBatchCreate,
) -> Any:
    """
    Create a draft payment batch for a given date range.
    Returns the batch along with eligible time entries for review.
    """
    return PaymentService.create_batch(session, current_user, batch_in)


@router.get("/batches/{batch_id}", response_model=PaymentBatchDetail)
def read_batch(
    session: SessionDep,
    current_user: CurrentUser,
    batch_id: uuid.UUID,
) -> Any:
    """
    Get a payment batch with its eligible time entries.
    """
    return PaymentService.get_batch(session, batch_id)


@router.post("/batches/{batch_id}/confirm", response_model=PaymentBatchPublic)
def confirm_batch(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    batch_id: uuid.UUID,
    confirm_in: ConfirmBatchIn,
) -> Any:
    """
    Confirm a draft batch. Provide lists of worklog IDs or freelancer IDs to exclude.
    Creates payment records for all remaining eligible entries.
    """
    return PaymentService.confirm_batch(session, batch_id, confirm_in)


@router.delete("/batches/{batch_id}", response_model=Message)
def delete_batch(
    session: SessionDep,
    current_user: CurrentUser,
    batch_id: uuid.UUID,
) -> Any:
    """
    Delete a draft payment batch (confirmed batches cannot be deleted).
    """
    PaymentService.delete_batch(session, batch_id)
    return Message(message="Payment batch deleted successfully")
