"""Service layer for freelancer portal operations."""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import case, extract, func
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


# Constants for validation
MAX_TIME_ENTRY_AGE_DAYS = 90  # Don't allow time entries older than 90 days
MAX_FUTURE_TIME_DAYS = 1  # Allow at most 1 day in the future (timezone tolerance)


class FreelancerPortalService:
    """Service for freelancer portal operations."""

    @staticmethod
    def get_dashboard_stats(
        session: Session,
        freelancer: Freelancer,
    ) -> FreelancerDashboardStats:
        """
        Get dashboard statistics for a freelancer.
        Optimized to use a single aggregated database query instead of N+1 queries.
        """
        freelancer_id = freelancer.id
        hourly_rate = freelancer.hourly_rate

        # Single aggregated query to get all stats
        # This replaces the N+1 query pattern with a single database call
        stats_query = (
            select(
                # Count worklogs by status using conditional aggregation
                func.count(WorkLog.id).label("total_worklogs"),
                func.sum(case((WorkLog.status == WorkLogStatus.PENDING, 1), else_=0)).label("pending_count"),
                func.sum(case((WorkLog.status == WorkLogStatus.APPROVED, 1), else_=0)).label("approved_count"),
                func.sum(case((WorkLog.status == WorkLogStatus.PAID, 1), else_=0)).label("paid_count"),
                func.sum(case((WorkLog.status == WorkLogStatus.REJECTED, 1), else_=0)).label("rejected_count"),
            )
            .where(WorkLog.freelancer_id == freelancer_id)
        )

        stats_result = session.exec(stats_query).one()

        # Get time-based aggregations with status breakdown
        time_stats_query = (
            select(
                func.coalesce(
                    func.sum(
                        extract('epoch', TimeEntry.end_time - TimeEntry.start_time) / 60
                    ),
                    0
                ).label("total_minutes"),
                func.coalesce(
                    func.sum(
                        case(
                            (WorkLog.status == WorkLogStatus.PAID,
                             extract('epoch', TimeEntry.end_time - TimeEntry.start_time) / 60),
                            else_=0
                        )
                    ),
                    0
                ).label("paid_minutes"),
                func.coalesce(
                    func.sum(
                        case(
                            (WorkLog.status.in_([WorkLogStatus.PENDING, WorkLogStatus.APPROVED]),
                             extract('epoch', TimeEntry.end_time - TimeEntry.start_time) / 60),
                            else_=0
                        )
                    ),
                    0
                ).label("pending_minutes"),
            )
            .select_from(TimeEntry)
            .join(WorkLog, TimeEntry.work_log_id == WorkLog.id)
            .where(WorkLog.freelancer_id == freelancer_id)
        )

        time_result = session.exec(time_stats_query).one()

        # Calculate amounts from minutes
        total_minutes = Decimal(str(time_result.total_minutes or 0))
        paid_minutes = Decimal(str(time_result.paid_minutes or 0))
        pending_minutes = Decimal(str(time_result.pending_minutes or 0))

        total_hours = (total_minutes / Decimal(60)).quantize(Decimal("0.01"))
        total_earned = ((paid_minutes / Decimal(60)) * hourly_rate).quantize(Decimal("0.01"))
        pending_amount = ((pending_minutes / Decimal(60)) * hourly_rate).quantize(Decimal("0.01"))

        return FreelancerDashboardStats(
            total_worklogs=stats_result.total_worklogs or 0,
            pending_worklogs=stats_result.pending_count or 0,
            approved_worklogs=stats_result.approved_count or 0,
            paid_worklogs=stats_result.paid_count or 0,
            rejected_worklogs=stats_result.rejected_count or 0,
            total_hours_logged=total_hours,
            total_earned=total_earned,
            pending_amount=pending_amount,
        )

    @staticmethod
    def get_my_worklogs(
        session: Session,
        freelancer: Freelancer,
        skip: int = 0,
        limit: int = 100,
        status: list[WorkLogStatus] | None = None,
    ) -> WorkLogsSummaryPublic:
        """
        Get worklogs for the current freelancer with aggregated data.
        Optimized to use a single query with JOIN instead of N+1 queries.
        """
        freelancer_id = freelancer.id

        # Build subquery for time entry aggregation
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

        # Main query with aggregated data
        query = (
            select(
                WorkLog.id,
                WorkLog.task_description,
                WorkLog.status,
                WorkLog.created_at,
                func.coalesce(duration_subquery.c.total_minutes, 0).label('total_duration_minutes'),
                func.coalesce(duration_subquery.c.entry_count, 0).label('time_entry_count'),
            )
            .outerjoin(duration_subquery, WorkLog.id == duration_subquery.c.work_log_id)
            .where(WorkLog.freelancer_id == freelancer_id)
        )

        if status:
            query = query.where(WorkLog.status.in_(status))

        # Get total count
        count_query = (
            select(func.count())
            .select_from(WorkLog)
            .where(WorkLog.freelancer_id == freelancer_id)
        )
        if status:
            count_query = count_query.where(WorkLog.status.in_(status))

        total_count = session.exec(count_query).one()

        # Get paginated results
        results = session.exec(
            query.order_by(WorkLog.created_at.desc()).offset(skip).limit(limit)
        ).all()

        # Build summaries from aggregated results
        summaries = []
        for row in results:
            total_minutes = int(row.total_duration_minutes or 0)
            total_amount = (
                Decimal(total_minutes) / Decimal(60) * freelancer.hourly_rate
            ).quantize(Decimal("0.01"))

            summaries.append(
                WorkLogSummary(
                    id=row.id,
                    task_description=row.task_description,
                    freelancer_id=freelancer_id,
                    freelancer_name=freelancer.name,
                    freelancer_email=freelancer.email,
                    hourly_rate=freelancer.hourly_rate,
                    status=row.status,
                    created_at=row.created_at,
                    total_duration_minutes=total_minutes,
                    total_amount=total_amount,
                    time_entry_count=row.time_entry_count or 0,
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

        # Create time entries with validation
        now = datetime.utcnow()
        min_allowed_time = now - timedelta(days=MAX_TIME_ENTRY_AGE_DAYS)
        max_allowed_time = now + timedelta(days=MAX_FUTURE_TIME_DAYS)

        for entry_data in data.time_entries:
            # Validate time order
            if entry_data.end_time <= entry_data.start_time:
                raise HTTPException(
                    status_code=400,
                    detail="End time must be after start time"
                )

            # Validate time bounds
            if entry_data.start_time < min_allowed_time:
                raise HTTPException(
                    status_code=400,
                    detail=f"Time entries cannot be older than {MAX_TIME_ENTRY_AGE_DAYS} days"
                )

            if entry_data.end_time > max_allowed_time:
                raise HTTPException(
                    status_code=400,
                    detail="Time entries cannot be in the future"
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

        # Validate time order
        if data.end_time <= data.start_time:
            raise HTTPException(
                status_code=400,
                detail="End time must be after start time"
            )

        # Validate time bounds
        now = datetime.utcnow()
        min_allowed_time = now - timedelta(days=MAX_TIME_ENTRY_AGE_DAYS)
        max_allowed_time = now + timedelta(days=MAX_FUTURE_TIME_DAYS)

        if data.start_time < min_allowed_time:
            raise HTTPException(
                status_code=400,
                detail=f"Time entries cannot be older than {MAX_TIME_ENTRY_AGE_DAYS} days"
            )

        if data.end_time > max_allowed_time:
            raise HTTPException(
                status_code=400,
                detail="Time entries cannot be in the future"
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
        """
        Get payment history for the freelancer.
        Optimized to use a single aggregated query.
        """
        freelancer_id = freelancer.id
        hourly_rate = freelancer.hourly_rate

        # Single query to get all payment info with aggregated amounts
        query = (
            select(
                PaymentBatch.id,
                PaymentBatch.processed_at,
                PaymentBatch.notes,
                PaymentBatch.status,
                func.count(WorkLog.id).label("worklog_count"),
                func.coalesce(
                    func.sum(
                        extract('epoch', TimeEntry.end_time - TimeEntry.start_time) / 60
                    ),
                    0
                ).label("total_minutes"),
            )
            .select_from(PaymentBatch)
            .join(WorkLog, PaymentBatch.id == WorkLog.payment_batch_id)
            .join(TimeEntry, WorkLog.id == TimeEntry.work_log_id)
            .where(WorkLog.freelancer_id == freelancer_id)
            .group_by(PaymentBatch.id)
            .order_by(PaymentBatch.processed_at.desc())
        )

        results = session.exec(query).all()

        payments = []
        for row in results:
            total_minutes = Decimal(str(row.total_minutes or 0))
            total_amount = ((total_minutes / Decimal(60)) * hourly_rate).quantize(Decimal("0.01"))

            payments.append(
                FreelancerPaymentInfo(
                    batch_id=row.id,
                    processed_at=row.processed_at,
                    total_amount=total_amount,
                    worklog_count=row.worklog_count,
                    notes=row.notes,
                    status=row.status,
                )
            )

        return payments
