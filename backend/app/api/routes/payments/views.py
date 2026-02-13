import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.api.routes.payments.service import PaymentService
from app.models import (
    Message,
    PaymentBatchCreate,
    PaymentBatchDetail,
    PaymentBatchPublic,
    PaymentBatchesPublic,
    PaymentsPublic,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/batches", dependencies=[Depends(get_current_active_superuser)], response_model=PaymentBatchesPublic)
def read_payment_batches(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    return PaymentService.get_batches(session, skip, limit)


@router.post("/batches", dependencies=[Depends(get_current_active_superuser)], response_model=PaymentBatchDetail)
def create_payment_batch(*, session: SessionDep, current_user: CurrentUser, batch_in: PaymentBatchCreate) -> Any:
    return PaymentService.create_batch(session, batch_in, current_user.id)


@router.get("/batches/{batch_id}", dependencies=[Depends(get_current_active_superuser)], response_model=PaymentBatchDetail)
def read_payment_batch(session: SessionDep, batch_id: uuid.UUID) -> Any:
    return PaymentService.get_batch(session, batch_id)


@router.get("/batches/{batch_id}/payments", dependencies=[Depends(get_current_active_superuser)], response_model=PaymentsPublic)
def read_batch_payments(session: SessionDep, batch_id: uuid.UUID) -> Any:
    return PaymentService.get_batch_payments(session, batch_id)


@router.post("/batches/{batch_id}/confirm", dependencies=[Depends(get_current_active_superuser)], response_model=PaymentBatchPublic)
def confirm_payment_batch(*, session: SessionDep, batch_id: uuid.UUID, selected_entry_ids: list[uuid.UUID]) -> Any:
    return PaymentService.confirm_batch(session, batch_id, selected_entry_ids)


@router.delete("/batches/{batch_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_payment_batch(session: SessionDep, batch_id: uuid.UUID) -> Message:
    return PaymentService.delete_batch(session, batch_id)
