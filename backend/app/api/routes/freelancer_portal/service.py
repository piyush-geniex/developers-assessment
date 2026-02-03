"""Service layer for freelancer portal operations."""
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.models import (
    Freelancer,
    FreelancerDashboardStats,
    FreelancerPaymentInfo,
    FreelancerTimeEntryCreate,
    FreelancerWorkLogCreate,
    FreelancerWorkLogUpdate,
    PaymentBatch,
    TimeEntry,
    TimeEntryPublic,
    TimeEntryUpdate,
    WorkLog,
    WorkLogDetail,
    WorkLogStatus,
    WorkLogSummary,
    WorkLogsSummaryPublic,
)


class FreelancerPortalService:
    """Service for freelancer portal operations."""

    @staticmethod
    def get_dashboard_stats(
        session: Session,
        freelancer: Freelancer,
    ) -> FreelancerDashboardStats:
        """Get dashboard statistics for a freelancer."""
        freelancer_id = freelancer.id

        # Count worklogs by status
        worklogs = session.exec(
            select(WorkLog).where(WorkLog.freelancer_id == freelancer_id)
        ).all()

        status_counts = {
            "pending": 0,
            "approved": 0,
            "paid": 0,
            "rejected": 0,
        }
        for wl in worklogs:
            status_counts[wl.status.value] += 1

        # Calculate hours and amounts
        total_hours = Decimal("0")
        total_earned = Decimal("0")
        pending_amount = Decimal("0")

        for wl in worklogs:
            # Get time entries for this worklog
            entries = session.exec(
                select(TimeEntry).where(TimeEntry.work_log_id == wl.id)
            ).all()

            total_minutes = sum(
                (e.end_time - e.start_time).total_seconds() / 60 for e in entries
            )
            hours = Decimal(total_minutes) / Decimal(60)
            amount = hours * freelancer.hourly_rate

            total_hours += hours

            if wl.status == WorkLogStatus.PAID:
                total_earned += amount
            elif wl.status in [WorkLogStatus.PENDING, WorkLogStatus.APPROVED]:
                pending_amount += amount

        return FreelancerDashboardStats(
            total_worklogs=len(worklogs),
            pending_worklogs=status_counts["pending"],
            approved_worklogs=status_counts["approved"],
            paid_worklogs=status_counts["paid"],
            rejected_worklogs=status_counts["rejected"],
            total_hours_logged=total_hours.quantize(Decimal("0.01")),
            total_earned=total_earned.quantize(Decimal("0.01")),
            pending_amount=pending_amount.quantize(Decimal("0.01")),
        )

    @staticmethod
    def get_my_worklogs(
        session: Session,
        freelancer: Freelancer,
        skip: int = 0,
        limit: int = 100,
        status: list[WorkLogStatus] | None = None,
    ) -> WorkLogsSummaryPublic:
        """Get worklogs for the current freelancer with aggregated data."""
        freelancer_id = freelancer.id

        # Build base query
        query = select(WorkLog).where(WorkLog.freelancer_id == freelancer_id)

        if status:
            query = query.where(WorkLog.status.in_(status))

        query = query.order_by(WorkLog.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_count = session.exec(count_query).one()

        # Get paginated results
        worklogs = session.exec(query.offset(skip).limit(limit)).all()

        # Build summary for each worklog
        summaries = []
        for wl in worklogs:
            entries = session.exec(
                select(TimeEntry).where(TimeEntry.work_log_id == wl.id)
            ).all()

            total_minutes = sum(
                int((e.end_time - e.start_time).total_seconds() / 60) for e in entries
            )
            total_amount = (
                Decimal(total_minutes) / Decimal(60) * freelancer.hourly_rate
            ).quantize(Decimal("0.01"))

            summaries.append(
                WorkLogSummary(
                    id=wl.id,
                    task_description=wl.task_description,
                    freelancer_id=freelancer_id,
                    freelancer_name=freelancer.name,
                    freelancer_email=freelancer.email,
                    hourly_rate=freelancer.hourly_rate,
                    status=wl.status,
                    created_at=wl.created_at,
                    total_duration_minutes=total_minutes,
                    total_amount=total_amount,
                    time_entry_count=len(entries),
                )
            )

        return WorkLogsSummaryPublic(data=summaries, count=total_count)

    @staticmethod
    def get_worklog_detail(
        session: Session,
        freelancer: Freelancer,
        worklog_id: uuid.UUID,
    ) -> WorkLogDetail:
        """Get detailed worklog information (must belong to freelancer)."""
        worklog = session.get(WorkLog, worklog_id)

        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        if worklog.freelancer_id != freelancer.id:
            raise HTTPException(
                status_code=403, detail="You don't have access to this worklog"
            )

        # Get time entries
        entries = session.exec(
            select(TimeEntry)
            .where(TimeEntry.work_log_id == worklog_id)
            .order_by(TimeEntry.start_time)
        ).all()

        # Calculate totals
        total_minutes = sum(
            int((e.end_time - e.start_time).total_seconds() / 60) for e in entries
        )
        total_amount = (
            Decimal(total_minutes) / Decimal(60) * freelancer.hourly_rate
        ).quantize(Decimal("0.01"))

        from app.models import FreelancerPublic

        return WorkLogDetail(
            id=worklog.id,
            task_description=worklog.task_description,
            freelancer_id=worklog.freelancer_id,
            status=worklog.status,
            payment_batch_id=worklog.payment_batch_id,
            created_at=worklog.created_at,
            updated_at=worklog.updated_at,
            freelancer=FreelancerPublic.model_validate(freelancer),
            time_entries=[TimeEntryPublic.model_validate(e) for e in entries],
            total_duration_minutes=total_minutes,
            total_amount=total_amount,
        )

    @staticmethod
    def create_worklog(
        session: Session,
        freelancer: Freelancer,
        data: FreelancerWorkLogCreate,
    ) -> WorkLogDetail:
        """Create a new worklog with time entries."""
        # Create the worklog
        worklog = WorkLog(
            freelancer_id=freelancer.id,
            task_description=data.task_description,
            status=WorkLogStatus.PENDING,
        )
        session.add(worklog)
        session.flush()  # Get the worklog ID

        # Create time entries
        for entry_data in data.time_entries:
            if entry_data.end_time <= entry_data.start_time:
                raise HTTPException(
                    status_code=400,
                    detail="End time must be after start time"
                )

            entry = TimeEntry(
                work_log_id=worklog.id,
                start_time=entry_data.start_time,
                end_time=entry_data.end_time,
                notes=entry_data.notes,
            )
            session.add(entry)

        session.commit()
        session.refresh(worklog)

        return FreelancerPortalService.get_worklog_detail(session, freelancer, worklog.id)

    @staticmethod
    def _check_worklog_editable(worklog: WorkLog) -> None:
        """Check if worklog can be edited (only PENDING status)."""
        if worklog.status != WorkLogStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot modify worklog with status '{worklog.status.value}'. Only PENDING worklogs can be edited."
            )

    @staticmethod
    def update_worklog(
        session: Session,
        freelancer: Freelancer,
        worklog_id: uuid.UUID,
        data: FreelancerWorkLogUpdate,
    ) -> WorkLogDetail:
        """Update a worklog (only if PENDING)."""
        worklog = session.get(WorkLog, worklog_id)

        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        if worklog.freelancer_id != freelancer.id:
            raise HTTPException(
                status_code=403, detail="You don't have access to this worklog"
            )

        FreelancerPortalService._check_worklog_editable(worklog)

        # Update fields
        if data.task_description is not None:
            worklog.task_description = data.task_description

        worklog.updated_at = datetime.utcnow()
        session.add(worklog)
        session.commit()

        return FreelancerPortalService.get_worklog_detail(session, freelancer, worklog_id)

    @staticmethod
    def delete_worklog(
        session: Session,
        freelancer: Freelancer,
        worklog_id: uuid.UUID,
    ) -> None:
        """Delete a worklog (only if PENDING)."""
        worklog = session.get(WorkLog, worklog_id)

        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        if worklog.freelancer_id != freelancer.id:
            raise HTTPException(
                status_code=403, detail="You don't have access to this worklog"
            )

        FreelancerPortalService._check_worklog_editable(worklog)

        session.delete(worklog)
        session.commit()

    @staticmethod
    def add_time_entry(
        session: Session,
        freelancer: Freelancer,
        worklog_id: uuid.UUID,
        data: FreelancerTimeEntryCreate,
    ) -> TimeEntryPublic:
        """Add a time entry to a worklog (only if PENDING)."""
        worklog = session.get(WorkLog, worklog_id)

        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        if worklog.freelancer_id != freelancer.id:
            raise HTTPException(
                status_code=403, detail="You don't have access to this worklog"
            )

        FreelancerPortalService._check_worklog_editable(worklog)

        if data.end_time <= data.start_time:
            raise HTTPException(
                status_code=400,
                detail="End time must be after start time"
            )

        entry = TimeEntry(
            work_log_id=worklog_id,
            start_time=data.start_time,
            end_time=data.end_time,
            notes=data.notes,
        )
        session.add(entry)

        # Update worklog timestamp
        worklog.updated_at = datetime.utcnow()
        session.add(worklog)

        session.commit()
        session.refresh(entry)

        return TimeEntryPublic.model_validate(entry)

    @staticmethod
    def update_time_entry(
        session: Session,
        freelancer: Freelancer,
        entry_id: uuid.UUID,
        data: TimeEntryUpdate,
    ) -> TimeEntryPublic:
        """Update a time entry (only if parent worklog is PENDING)."""
        entry = session.get(TimeEntry, entry_id)

        if not entry:
            raise HTTPException(status_code=404, detail="Time entry not found")

        worklog = session.get(WorkLog, entry.work_log_id)

        if worklog.freelancer_id != freelancer.id:
            raise HTTPException(
                status_code=403, detail="You don't have access to this time entry"
            )

        FreelancerPortalService._check_worklog_editable(worklog)

        # Update fields
        if data.start_time is not None:
            entry.start_time = data.start_time
        if data.end_time is not None:
            entry.end_time = data.end_time
        if data.notes is not None:
            entry.notes = data.notes

        # Validate times
        if entry.end_time <= entry.start_time:
            raise HTTPException(
                status_code=400,
                detail="End time must be after start time"
            )

        session.add(entry)

        # Update worklog timestamp
        worklog.updated_at = datetime.utcnow()
        session.add(worklog)

        session.commit()
        session.refresh(entry)

        return TimeEntryPublic.model_validate(entry)

    @staticmethod
    def delete_time_entry(
        session: Session,
        freelancer: Freelancer,
        entry_id: uuid.UUID,
    ) -> None:
        """Delete a time entry (only if parent worklog is PENDING)."""
        entry = session.get(TimeEntry, entry_id)

        if not entry:
            raise HTTPException(status_code=404, detail="Time entry not found")

        worklog = session.get(WorkLog, entry.work_log_id)

        if worklog.freelancer_id != freelancer.id:
            raise HTTPException(
                status_code=403, detail="You don't have access to this time entry"
            )

        FreelancerPortalService._check_worklog_editable(worklog)

        # Check if this is the last entry
        entry_count = session.exec(
            select(func.count())
            .select_from(TimeEntry)
            .where(TimeEntry.work_log_id == worklog.id)
        ).one()

        if entry_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last time entry. Delete the worklog instead."
            )

        session.delete(entry)

        # Update worklog timestamp
        worklog.updated_at = datetime.utcnow()
        session.add(worklog)

        session.commit()

    @staticmethod
    def get_my_payments(
        session: Session,
        freelancer: Freelancer,
    ) -> list[FreelancerPaymentInfo]:
        """Get payment history for the freelancer."""
        # Find all payment batches that include this freelancer's worklogs
        query = (
            select(PaymentBatch, func.count(WorkLog.id).label("worklog_count"))
            .join(WorkLog, PaymentBatch.id == WorkLog.payment_batch_id)
            .where(WorkLog.freelancer_id == freelancer.id)
            .group_by(PaymentBatch.id)
            .order_by(PaymentBatch.processed_at.desc())
        )

        results = session.exec(query).all()

        payments = []
        for batch, worklog_count in results:
            # Calculate amount for this freelancer in this batch
            freelancer_worklogs = session.exec(
                select(WorkLog)
                .where(WorkLog.payment_batch_id == batch.id)
                .where(WorkLog.freelancer_id == freelancer.id)
            ).all()

            total_amount = Decimal("0")
            for wl in freelancer_worklogs:
                entries = session.exec(
                    select(TimeEntry).where(TimeEntry.work_log_id == wl.id)
                ).all()
                total_minutes = sum(
                    (e.end_time - e.start_time).total_seconds() / 60 for e in entries
                )
                total_amount += (
                    Decimal(total_minutes) / Decimal(60) * freelancer.hourly_rate
                )

            payments.append(
                FreelancerPaymentInfo(
                    batch_id=batch.id,
                    processed_at=batch.processed_at,
                    total_amount=total_amount.quantize(Decimal("0.01")),
                    worklog_count=len(freelancer_worklogs),
                    notes=batch.notes,
                    status=batch.status,
                )
            )

        return payments
