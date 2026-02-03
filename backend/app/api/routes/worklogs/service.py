import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import extract, func
from sqlmodel import Session, select

from app.models import (
    Freelancer,
    TimeEntry,
    WorkLog,
    WorkLogCreate,
    WorkLogDetail,
    WorkLogPublic,
    WorkLogsPublic,
    WorkLogStatus,
    WorkLogSummary,
    WorkLogsSummaryPublic,
    WorkLogUpdate,
    TimeEntryPublic,
    FreelancerPublic,
)


class WorkLogService:
    # Valid status transitions
    VALID_TRANSITIONS = {
        WorkLogStatus.PENDING: [WorkLogStatus.APPROVED, WorkLogStatus.REJECTED],
        WorkLogStatus.APPROVED: [WorkLogStatus.PENDING, WorkLogStatus.PAID, WorkLogStatus.REJECTED],
        WorkLogStatus.REJECTED: [WorkLogStatus.PENDING],
        WorkLogStatus.PAID: [],  # Cannot change from PAID
    }

    @staticmethod
    def get_worklogs(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        freelancer_id: uuid.UUID | None = None,
        status: WorkLogStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> WorkLogsPublic:
        """Retrieve worklogs with filters."""
        query = select(WorkLog)
        count_query = select(func.count()).select_from(WorkLog)

        if freelancer_id:
            query = query.where(WorkLog.freelancer_id == freelancer_id)
            count_query = count_query.where(WorkLog.freelancer_id == freelancer_id)

        if status:
            query = query.where(WorkLog.status == status)
            count_query = count_query.where(WorkLog.status == status)

        if date_from:
            query = query.where(WorkLog.created_at >= date_from)
            count_query = count_query.where(WorkLog.created_at >= date_from)

        if date_to:
            query = query.where(WorkLog.created_at <= date_to)
            count_query = count_query.where(WorkLog.created_at <= date_to)

        count = session.exec(count_query).one()
        worklogs = session.exec(
            query.order_by(WorkLog.created_at.desc()).offset(skip).limit(limit)
        ).all()

        return WorkLogsPublic(data=worklogs, count=count)

    @staticmethod
    def get_worklogs_summary(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        freelancer_id: uuid.UUID | None = None,
        status: list[WorkLogStatus] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> WorkLogsSummaryPublic:
        """
        Get aggregated worklog summary with calculated totals.
        This is the KEY endpoint for the dashboard - calculations done in DB.
        """
        # Build the aggregation query
        # Calculate total minutes using EXTRACT for each time entry
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

        # Main query joining WorkLog, Freelancer, and the duration subquery
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
        )

        # Apply filters
        if freelancer_id:
            query = query.where(WorkLog.freelancer_id == freelancer_id)

        if status:
            query = query.where(WorkLog.status.in_(status))

        if date_from:
            # Filter by time entries date range for accurate filtering
            subq = select(TimeEntry.work_log_id).where(TimeEntry.start_time >= date_from).distinct()
            query = query.where(WorkLog.id.in_(subq))

        if date_to:
            subq = select(TimeEntry.work_log_id).where(TimeEntry.end_time <= date_to).distinct()
            query = query.where(WorkLog.id.in_(subq))

        # Get count
        count_query = (
            select(func.count(func.distinct(WorkLog.id)))
            .select_from(WorkLog)
            .join(Freelancer, WorkLog.freelancer_id == Freelancer.id)
        )
        if freelancer_id:
            count_query = count_query.where(WorkLog.freelancer_id == freelancer_id)
        if status:
            count_query = count_query.where(WorkLog.status.in_(status))
        if date_from:
            subq = select(TimeEntry.work_log_id).where(TimeEntry.start_time >= date_from).distinct()
            count_query = count_query.where(WorkLog.id.in_(subq))
        if date_to:
            subq = select(TimeEntry.work_log_id).where(TimeEntry.end_time <= date_to).distinct()
            count_query = count_query.where(WorkLog.id.in_(subq))

        count = session.exec(count_query).one()

        # Execute main query with pagination
        results = session.exec(
            query.order_by(WorkLog.created_at.desc()).offset(skip).limit(limit)
        ).all()

        # Transform to WorkLogSummary objects
        summaries = []
        for row in results:
            total_minutes = int(row.total_duration_minutes or 0)
            hourly_rate = Decimal(str(row.hourly_rate))
            # Calculate amount: (minutes / 60) * hourly_rate
            total_amount = (Decimal(total_minutes) / Decimal(60)) * hourly_rate

            summaries.append(
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

        return WorkLogsSummaryPublic(data=summaries, count=count)

    @staticmethod
    def get_worklog(session: Session, worklog_id: uuid.UUID) -> WorkLogPublic:
        """Get a worklog by ID."""
        worklog = session.get(WorkLog, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")
        return worklog

    @staticmethod
    def get_worklog_detail(session: Session, worklog_id: uuid.UUID) -> WorkLogDetail:
        """Get a worklog with all details including time entries and calculated totals."""
        worklog = session.get(WorkLog, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        # Get freelancer
        freelancer = session.get(Freelancer, worklog.freelancer_id)

        # Get time entries
        time_entries = session.exec(
            select(TimeEntry)
            .where(TimeEntry.work_log_id == worklog_id)
            .order_by(TimeEntry.start_time)
        ).all()

        # Calculate totals
        total_minutes = 0
        time_entry_publics = []
        for entry in time_entries:
            duration = int((entry.end_time - entry.start_time).total_seconds() / 60)
            total_minutes += duration
            time_entry_publics.append(
                TimeEntryPublic(
                    id=entry.id,
                    work_log_id=entry.work_log_id,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                    notes=entry.notes,
                    duration_minutes=duration,
                    created_at=entry.created_at,
                )
            )

        hourly_rate = Decimal(str(freelancer.hourly_rate))
        total_amount = (Decimal(total_minutes) / Decimal(60)) * hourly_rate

        return WorkLogDetail(
            id=worklog.id,
            task_description=worklog.task_description,
            freelancer_id=worklog.freelancer_id,
            status=worklog.status,
            payment_batch_id=worklog.payment_batch_id,
            created_at=worklog.created_at,
            updated_at=worklog.updated_at,
            freelancer=FreelancerPublic(
                id=freelancer.id,
                name=freelancer.name,
                email=freelancer.email,
                hourly_rate=freelancer.hourly_rate,
                is_active=freelancer.is_active,
                created_at=freelancer.created_at,
                updated_at=freelancer.updated_at,
            ),
            time_entries=time_entry_publics,
            total_duration_minutes=total_minutes,
            total_amount=total_amount.quantize(Decimal('0.01')),
        )

    @staticmethod
    def create_worklog(session: Session, worklog_in: WorkLogCreate) -> WorkLogPublic:
        """Create a new worklog."""
        # Verify freelancer exists
        freelancer = session.get(Freelancer, worklog_in.freelancer_id)
        if not freelancer:
            raise HTTPException(status_code=404, detail="Freelancer not found")

        worklog = WorkLog.model_validate(worklog_in)
        session.add(worklog)
        session.commit()
        session.refresh(worklog)
        return worklog

    @staticmethod
    def update_worklog(
        session: Session, worklog_id: uuid.UUID, worklog_in: WorkLogUpdate
    ) -> WorkLogPublic:
        """Update a worklog."""
        worklog = session.get(WorkLog, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        # Validate status transition if status is being changed
        if worklog_in.status and worklog_in.status != worklog.status:
            valid_next_states = WorkLogService.VALID_TRANSITIONS.get(worklog.status, [])
            if worklog_in.status not in valid_next_states:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot transition from {worklog.status.value} to {worklog_in.status.value}. "
                    f"Valid transitions: {[s.value for s in valid_next_states]}"
                )

        update_data = worklog_in.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        worklog.sqlmodel_update(update_data)
        session.add(worklog)
        session.commit()
        session.refresh(worklog)
        return worklog

    @staticmethod
    def update_worklog_status(
        session: Session, worklog_id: uuid.UUID, new_status: WorkLogStatus
    ) -> WorkLogPublic:
        """Update worklog status with validation."""
        worklog = session.get(WorkLog, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        valid_next_states = WorkLogService.VALID_TRANSITIONS.get(worklog.status, [])
        if new_status not in valid_next_states:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {worklog.status.value} to {new_status.value}. "
                f"Valid transitions: {[s.value for s in valid_next_states]}"
            )

        worklog.status = new_status
        worklog.updated_at = datetime.utcnow()
        session.add(worklog)
        session.commit()
        session.refresh(worklog)
        return worklog

    @staticmethod
    def delete_worklog(session: Session, worklog_id: uuid.UUID) -> None:
        """Delete a worklog."""
        worklog = session.get(WorkLog, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")
        if worklog.status == WorkLogStatus.PAID:
            raise HTTPException(
                status_code=400, detail="Cannot delete a paid worklog"
            )
        session.delete(worklog)
        session.commit()

    @staticmethod
    def bulk_update_status(
        session: Session, worklog_ids: list[uuid.UUID], new_status: WorkLogStatus
    ) -> list[WorkLogPublic]:
        """Bulk update worklog status."""
        updated = []
        for worklog_id in worklog_ids:
            try:
                worklog = WorkLogService.update_worklog_status(session, worklog_id, new_status)
                updated.append(worklog)
            except HTTPException:
                # Skip invalid transitions
                continue
        return updated
