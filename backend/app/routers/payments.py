"""
Payments API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from sqlalchemy import and_
from typing import List
from datetime import datetime
from decimal import Decimal
import uuid

from ..database import get_session
from ..models import (
    Payment, PaymentBatch, Worklog, Freelancer, Task,
    PaymentRead, PaymentBatchRead, PaymentBatchWithPayments,
    PaymentPreviewRequest, PaymentPreviewResponse,
    PaymentProcessRequest, PaymentProcessResponse,
    WorklogRead
)

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/preview", response_model=PaymentPreviewResponse)
async def preview_payment_batch(
    request: PaymentPreviewRequest,
    session: Session = Depends(get_session)
) -> PaymentPreviewResponse:
    """
    Preview a payment batch before processing.
    Returns all eligible worklogs with exclusions applied.
    """
    # Get eligible worklogs
    statement = (
        select(
            Worklog,
            Freelancer.name.label("freelancer_name"),
            Freelancer.email.label("freelancer_email"),
            Freelancer.hourly_rate.label("freelancer_hourly_rate"),
            Task.title.label("task_title"),
        )
        .join(Freelancer, Worklog.freelancer_id == Freelancer.id)
        .join(Task, Worklog.task_id == Task.id)
        .where(
            and_(
                Worklog.status == "pending",
                func.date(Worklog.created_at) >= request.date_from,
                func.date(Worklog.created_at) <= request.date_to
            )
        )
    )
    
    # Apply exclusions
    if request.excluded_worklog_ids:
        statement = statement.where(Worklog.id.notin_(request.excluded_worklog_ids))
    if request.excluded_freelancer_ids:
        statement = statement.where(Worklog.freelancer_id.notin_(request.excluded_freelancer_ids))
    
    statement = statement.order_by(Worklog.created_at.desc())
    results = session.exec(statement).all()
    
    # Build response
    worklogs = []
    total_amount = Decimal("0")
    freelancer_ids = set()
    
    for row in results:
        worklog = row[0]
        total_amount += worklog.total_amount
        freelancer_ids.add(worklog.freelancer_id)
        
        worklog_data = WorklogRead(
            id=worklog.id,
            freelancer_id=worklog.freelancer_id,
            task_id=worklog.task_id,
            description=worklog.description,
            total_hours=worklog.total_hours,
            total_amount=worklog.total_amount,
            status=worklog.status,
            created_at=worklog.created_at,
            freelancer_name=row.freelancer_name,
            freelancer_email=row.freelancer_email,
            freelancer_hourly_rate=row.freelancer_hourly_rate,
            task_title=row.task_title
        )
        worklogs.append(worklog_data)
    
    return PaymentPreviewResponse(
        date_from=request.date_from,
        date_to=request.date_to,
        worklogs=worklogs,
        total_amount=total_amount,
        total_worklogs=len(worklogs),
        freelancers_count=len(freelancer_ids),
        excluded_worklog_ids=request.excluded_worklog_ids,
        excluded_freelancer_ids=request.excluded_freelancer_ids
    )


@router.post("/process", response_model=PaymentProcessResponse)
async def process_payment_batch(
    request: PaymentProcessRequest,
    session: Session = Depends(get_session)
) -> PaymentProcessResponse:
    """
    Process a payment batch. Creates payment records and marks worklogs as paid.
    """
    # Get eligible worklogs (same logic as preview)
    statement = (
        select(Worklog)
        .where(
            and_(
                Worklog.status == "pending",
                func.date(Worklog.created_at) >= request.date_from,
                func.date(Worklog.created_at) <= request.date_to
            )
        )
    )
    
    if request.excluded_worklog_ids:
        statement = statement.where(Worklog.id.notin_(request.excluded_worklog_ids))
    if request.excluded_freelancer_ids:
        statement = statement.where(Worklog.freelancer_id.notin_(request.excluded_freelancer_ids))
    
    worklogs = session.exec(statement).all()
    
    if not worklogs:
        raise HTTPException(status_code=400, detail="No eligible worklogs for payment")
    
    # Calculate totals
    total_amount = sum(w.total_amount for w in worklogs)
    freelancer_ids = set(w.freelancer_id for w in worklogs)
    
    # Create payment batch
    batch = PaymentBatch(
        date_from=request.date_from,
        date_to=request.date_to,
        total_amount=total_amount,
        status="completed",
        processed_at=datetime.utcnow()
    )
    session.add(batch)
    session.flush()  # Get the batch ID
    
    # Create payments and update worklogs
    payments = []
    for worklog in worklogs:
        # Create payment
        payment = Payment(
            batch_id=batch.id,
            worklog_id=worklog.id,
            freelancer_id=worklog.freelancer_id,
            amount=worklog.total_amount,
            status="completed"
        )
        session.add(payment)
        
        # Update worklog status
        worklog.status = "paid"
        session.add(worklog)
        
        # Get freelancer name for response
        freelancer = session.get(Freelancer, worklog.freelancer_id)
        task_stmt = select(Task).where(Task.id == worklog.task_id)
        task = session.exec(task_stmt).first()
        
        payments.append(PaymentRead(
            id=payment.id,
            batch_id=payment.batch_id,
            worklog_id=payment.worklog_id,
            freelancer_id=payment.freelancer_id,
            amount=payment.amount,
            status=payment.status,
            created_at=payment.created_at,
            freelancer_name=freelancer.name if freelancer else None,
            worklog_description=worklog.description,
            task_title=task.title if task else None
        ))
    
    session.commit()
    
    return PaymentProcessResponse(
        batch=PaymentBatchRead(
            id=batch.id,
            date_from=batch.date_from,
            date_to=batch.date_to,
            total_amount=batch.total_amount,
            status=batch.status,
            created_at=batch.created_at,
            processed_at=batch.processed_at,
            payments_count=len(payments)
        ),
        payments=payments,
        total_amount=total_amount,
        worklogs_paid=len(worklogs),
        freelancers_paid=len(freelancer_ids)
    )


@router.get("/batches", response_model=List[PaymentBatchRead])
async def get_payment_batches(
    session: Session = Depends(get_session)
) -> List[PaymentBatchRead]:
    """
    Get all payment batches with payment counts.
    """
    statement = select(PaymentBatch).order_by(PaymentBatch.created_at.desc())
    batches = session.exec(statement).all()
    
    result = []
    for batch in batches:
        # Count payments in batch
        count_stmt = select(func.count(Payment.id)).where(Payment.batch_id == batch.id)
        payments_count = session.exec(count_stmt).first() or 0
        
        result.append(PaymentBatchRead(
            id=batch.id,
            date_from=batch.date_from,
            date_to=batch.date_to,
            total_amount=batch.total_amount,
            status=batch.status,
            created_at=batch.created_at,
            processed_at=batch.processed_at,
            payments_count=payments_count
        ))
    
    return result


@router.get("/batches/{batch_id}", response_model=PaymentBatchWithPayments)
async def get_payment_batch(
    batch_id: uuid.UUID,
    session: Session = Depends(get_session)
) -> PaymentBatchWithPayments:
    """
    Get a specific payment batch with all payment details.
    """
    batch = session.get(PaymentBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Payment batch not found")
    
    # Get all payments in batch
    payments_stmt = (
        select(
            Payment,
            Freelancer.name.label("freelancer_name"),
            Worklog.description.label("worklog_description"),
            Task.title.label("task_title")
        )
        .join(Freelancer, Payment.freelancer_id == Freelancer.id)
        .join(Worklog, Payment.worklog_id == Worklog.id)
        .join(Task, Worklog.task_id == Task.id)
        .where(Payment.batch_id == batch_id)
        .order_by(Payment.created_at)
    )
    
    results = session.exec(payments_stmt).all()
    
    payments = []
    for row in results:
        payment = row[0]
        payments.append(PaymentRead(
            id=payment.id,
            batch_id=payment.batch_id,
            worklog_id=payment.worklog_id,
            freelancer_id=payment.freelancer_id,
            amount=payment.amount,
            status=payment.status,
            created_at=payment.created_at,
            freelancer_name=row.freelancer_name,
            worklog_description=row.worklog_description,
            task_title=row.task_title
        ))
    
    return PaymentBatchWithPayments(
        id=batch.id,
        date_from=batch.date_from,
        date_to=batch.date_to,
        total_amount=batch.total_amount,
        status=batch.status,
        created_at=batch.created_at,
        processed_at=batch.processed_at,
        payments=payments
    )
