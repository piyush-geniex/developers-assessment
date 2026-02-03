import uuid
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import extract, func
from sqlmodel import Session, select

from app.models import (
    Freelancer,
    FreelancerPaymentSummary,
    PaymentBatch,
    PaymentBatchDetail,
    PaymentBatchesPublic,
    PaymentBatchPublic,
    PaymentBatchStatus,
    PaymentIssue,
    PaymentPreviewResponse,
    PaymentProcessRequest,
    PaymentProcessResponse,
    TimeEntry,
    User,
    WorkLog,
    WorkLogStatus,
    WorkLogSummary,
)


class PaymentService:
    @staticmethod
    def get_payment_batches(
        session: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> PaymentBatchesPublic:
        """Retrieve payment batch history."""
        count = session.exec(
            select(func.count()).select_from(PaymentBatch)
        ).one()

        batches = session.exec(
            select(PaymentBatch)
            .order_by(PaymentBatch.processed_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()

        # Add worklog counts
        data = []
        for batch in batches:
            worklog_count = session.exec(
                select(func.count())
                .select_from(WorkLog)
                .where(WorkLog.payment_batch_id == batch.id)
            ).one()
            data.append(
                PaymentBatchPublic(
                    id=batch.id,
                    processed_at=batch.processed_at,
                    processed_by_id=batch.processed_by_id,
                    total_amount=batch.total_amount,
                    status=batch.status,
                    notes=batch.notes,
                    worklog_count=worklog_count,
                )
            )

        return PaymentBatchesPublic(data=data, count=count)

    @staticmethod
    def get_payment_batch(
        session: Session, batch_id: uuid.UUID
    ) -> PaymentBatchDetail:
        """Get payment batch with details."""
        batch = session.get(PaymentBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Payment batch not found")

        # Get associated worklogs
        worklogs = session.exec(
            select(WorkLog).where(WorkLog.payment_batch_id == batch_id)
        ).all()

        return PaymentBatchDetail(
            id=batch.id,
            processed_at=batch.processed_at,
            processed_by_id=batch.processed_by_id,
            total_amount=batch.total_amount,
            status=batch.status,
            notes=batch.notes,
            worklog_count=len(worklogs),
            worklogs=worklogs,
        )

    @staticmethod
    def preview_payment(
        session: Session,
        worklog_ids: list[uuid.UUID],
    ) -> PaymentPreviewResponse:
        """
        Preview payment for selected worklogs.
        Validates selection and returns detailed breakdown.
        """
        if not worklog_ids:
            raise HTTPException(
                status_code=400, detail="No worklogs selected for payment"
            )

        issues: list[PaymentIssue] = []
        valid_worklogs: list[WorkLogSummary] = []

        # Build aggregation query for selected worklogs
        duration_subquery = (
            select(
                TimeEntry.work_log_id,
                func.coalesce(
                    func.sum(
                        extract('epoch', TimeEntry.end_time - TimeEntry.start_time) / 60
                    ),
                    0
                ).label('total_minutes'),
                func.count(TimeEntry.id).label('entry_count')
            )
            .group_by(TimeEntry.work_log_id)
            .subquery()
        )

        query = (
            select(
                WorkLog.id,
                WorkLog.task_description,
                WorkLog.freelancer_id,
                WorkLog.status,
                WorkLog.created_at,
                Freelancer.name.label('freelancer_name'),
                Freelancer.email.label('freelancer_email'),
                Freelancer.hourly_rate,
                func.coalesce(duration_subquery.c.total_minutes, 0).label('total_duration_minutes'),
                func.coalesce(duration_subquery.c.entry_count, 0).label('time_entry_count'),
            )
            .join(Freelancer, WorkLog.freelancer_id == Freelancer.id)
            .outerjoin(duration_subquery, WorkLog.id == duration_subquery.c.work_log_id)
            .where(WorkLog.id.in_(worklog_ids))
        )

        results = session.exec(query).all()

        # Check for missing worklogs
        found_ids = {row.id for row in results}
        for wl_id in worklog_ids:
            if wl_id not in found_ids:
                issues.append(
                    PaymentIssue(
                        worklog_id=wl_id,
                        issue_type="NOT_FOUND",
                        message=f"Worklog {wl_id} not found",
                    )
                )

        for row in results:
            total_minutes = int(row.total_duration_minutes or 0)
            hourly_rate = Decimal(str(row.hourly_rate))
            total_amount = (Decimal(total_minutes) / Decimal(60)) * hourly_rate

            # Check for issues
            if row.status == WorkLogStatus.PAID:
                issues.append(
                    PaymentIssue(
                        worklog_id=row.id,
                        issue_type="ALREADY_PAID",
                        message=f"Worklog '{row.task_description[:30]}...' is already paid",
                    )
                )
                continue

            if row.status == WorkLogStatus.REJECTED:
                issues.append(
                    PaymentIssue(
                        worklog_id=row.id,
                        issue_type="REJECTED",
                        message=f"Worklog '{row.task_description[:30]}...' is rejected",
                    )
                )
                continue

            if total_minutes == 0:
                issues.append(
                    PaymentIssue(
                        worklog_id=row.id,
                        issue_type="ZERO_DURATION",
                        message=f"Worklog '{row.task_description[:30]}...' has no time entries",
                    )
                )
                # Still add to valid (user might want to pay anyway)

            valid_worklogs.append(
                WorkLogSummary(
                    id=row.id,
                    task_description=row.task_description,
                    freelancer_id=row.freelancer_id,
                    freelancer_name=row.freelancer_name,
                    freelancer_email=row.freelancer_email,
                    hourly_rate=hourly_rate,
                    status=row.status,
                    created_at=row.created_at,
                    total_duration_minutes=total_minutes,
                    total_amount=total_amount.quantize(Decimal('0.01')),
                    time_entry_count=row.time_entry_count or 0,
                )
            )

        # Group by freelancer
        freelancer_groups: dict[uuid.UUID, list[WorkLogSummary]] = defaultdict(list)
        for wl in valid_worklogs:
            freelancer_groups[wl.freelancer_id].append(wl)

        freelancer_breakdown = []
        for freelancer_id, worklogs in freelancer_groups.items():
            first_wl = worklogs[0]
            total_minutes = sum(wl.total_duration_minutes for wl in worklogs)
            total_amount = sum(wl.total_amount for wl in worklogs)

            freelancer_breakdown.append(
                FreelancerPaymentSummary(
                    freelancer_id=freelancer_id,
                    freelancer_name=first_wl.freelancer_name,
                    freelancer_email=first_wl.freelancer_email,
                    hourly_rate=first_wl.hourly_rate,
                    worklog_count=len(worklogs),
                    total_duration_minutes=total_minutes,
                    total_amount=total_amount,
                    worklogs=worklogs,
                )
            )

        # Sort by name
        freelancer_breakdown.sort(key=lambda x: x.freelancer_name)

        total_amount = sum(fb.total_amount for fb in freelancer_breakdown)

        # Can process if we have valid worklogs and no blocking issues
        blocking_issues = [i for i in issues if i.issue_type in ("ALREADY_PAID", "REJECTED", "NOT_FOUND")]
        can_process = len(valid_worklogs) > 0 and len(blocking_issues) == 0

        return PaymentPreviewResponse(
            total_worklogs=len(valid_worklogs),
            total_amount=total_amount,
            freelancer_breakdown=freelancer_breakdown,
            issues=issues,
            can_process=can_process,
        )

    @staticmethod
    def process_payment(
        session: Session,
        current_user: User,
        request: PaymentProcessRequest,
    ) -> PaymentProcessResponse:
        """
        Process payment for selected worklogs.
        Creates a payment batch and updates worklog statuses.
        """
        if not request.worklog_ids:
            raise HTTPException(
                status_code=400, detail="No worklogs selected for payment"
            )

        # Get preview to validate
        preview = PaymentService.preview_payment(session, request.worklog_ids)

        if not preview.can_process:
            raise HTTPException(
                status_code=400,
                detail="Cannot process payment. Check issues in preview.",
            )

        # Create payment batch
        batch = PaymentBatch(
            processed_by_id=current_user.id,
            total_amount=preview.total_amount,
            status=PaymentBatchStatus.COMPLETED,
            notes=request.notes,
        )
        session.add(batch)
        session.flush()  # Get the batch ID

        # Update worklogs
        valid_ids = [wl.id for fb in preview.freelancer_breakdown for wl in fb.worklogs]
        for worklog_id in valid_ids:
            worklog = session.get(WorkLog, worklog_id)
            if worklog and worklog.status != WorkLogStatus.PAID:
                worklog.status = WorkLogStatus.PAID
                worklog.payment_batch_id = batch.id
                worklog.updated_at = datetime.utcnow()
                session.add(worklog)

        session.commit()
        session.refresh(batch)

        return PaymentProcessResponse(
            batch_id=batch.id,
            total_worklogs=preview.total_worklogs,
            total_amount=preview.total_amount,
            status=batch.status,
        )
