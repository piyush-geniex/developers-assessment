from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.payments.service import PaymentService
from app.models import (
    ConfirmPaymentRequest,
    PaymentBatchPreview,
    RemittancePublic,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/preview", response_model=PaymentBatchPreview)
def get_payment_preview(
    session: SessionDep,
    current_user: CurrentUser,
    date_from: str = Query(..., description="Period start (YYYY-MM-DD)"),
    date_to: str = Query(..., description="Period end (YYYY-MM-DD)"),
) -> Any:
    """
    Get worklogs eligible for payment in the given date range (unremitted only).
    Use this to review selection before confirming payment.
    """
    return PaymentService.get_payment_preview(
        session, current_user, date_from, date_to
    )


@router.post("/confirm", response_model=list[RemittancePublic])
def confirm_payment(
    session: SessionDep,
    current_user: CurrentUser,
    body: ConfirmPaymentRequest,
) -> Any:
    """
    Create remittances for the selected worklogs. Exclude worklogs by omitting
    them from include_work_log_ids, or exclude entire freelancers via
    exclude_freelancer_ids.
    """
    return PaymentService.confirm_payment(session, current_user, body)
