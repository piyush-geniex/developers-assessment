import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    TimeEntry,
    TimeEntryCreate,
    TimeEntryPublic,
    TimeEntriesPublic,
    TimeEntryUpdate,
    WorkLog,
    WorkLogStatus,
)


class TimeEntryService:
    @staticmethod
    def get_time_entries(
        session: Session,
        work_log_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> TimeEntriesPublic:
        """Retrieve time entries with optional filtering by worklog."""
        query = select(TimeEntry)
        count_query = select(func.count()).select_from(TimeEntry)

        if work_log_id:
            query = query.where(TimeEntry.work_log_id == work_log_id)
            count_query = count_query.where(TimeEntry.work_log_id == work_log_id)

        count = session.exec(count_query).one()
        entries = session.exec(
            query.order_by(TimeEntry.start_time.desc()).offset(skip).limit(limit)
        ).all()

        # Convert to public with calculated duration
        data = []
        for entry in entries:
            duration = int((entry.end_time - entry.start_time).total_seconds() / 60)
            data.append(
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

        return TimeEntriesPublic(data=data, count=count)

    @staticmethod
    def get_time_entry(session: Session, entry_id: uuid.UUID) -> TimeEntryPublic:
        """Get a time entry by ID."""
        entry = session.get(TimeEntry, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Time entry not found")

        duration = int((entry.end_time - entry.start_time).total_seconds() / 60)
        return TimeEntryPublic(
            id=entry.id,
            work_log_id=entry.work_log_id,
            start_time=entry.start_time,
            end_time=entry.end_time,
            notes=entry.notes,
            duration_minutes=duration,
            created_at=entry.created_at,
        )

    @staticmethod
    def create_time_entry(
        session: Session, entry_in: TimeEntryCreate
    ) -> TimeEntryPublic:
        """Create a new time entry."""
        # Verify worklog exists
        worklog = session.get(WorkLog, entry_in.work_log_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        # Cannot add entries to paid worklogs
        if worklog.status == WorkLogStatus.PAID:
            raise HTTPException(
                status_code=400, detail="Cannot add entries to a paid worklog"
            )

        # Validate times
        if entry_in.end_time <= entry_in.start_time:
            raise HTTPException(
                status_code=400, detail="End time must be after start time"
            )

        entry = TimeEntry.model_validate(entry_in)
        session.add(entry)
        session.commit()
        session.refresh(entry)

        duration = int((entry.end_time - entry.start_time).total_seconds() / 60)
        return TimeEntryPublic(
            id=entry.id,
            work_log_id=entry.work_log_id,
            start_time=entry.start_time,
            end_time=entry.end_time,
            notes=entry.notes,
            duration_minutes=duration,
            created_at=entry.created_at,
        )

    @staticmethod
    def update_time_entry(
        session: Session, entry_id: uuid.UUID, entry_in: TimeEntryUpdate
    ) -> TimeEntryPublic:
        """Update a time entry."""
        entry = session.get(TimeEntry, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Time entry not found")

        # Check if worklog is paid
        worklog = session.get(WorkLog, entry.work_log_id)
        if worklog.status == WorkLogStatus.PAID:
            raise HTTPException(
                status_code=400, detail="Cannot modify entries in a paid worklog"
            )

        # Validate times if both are provided
        start_time = entry_in.start_time if entry_in.start_time else entry.start_time
        end_time = entry_in.end_time if entry_in.end_time else entry.end_time
        if end_time <= start_time:
            raise HTTPException(
                status_code=400, detail="End time must be after start time"
            )

        update_data = entry_in.model_dump(exclude_unset=True)
        entry.sqlmodel_update(update_data)
        session.add(entry)
        session.commit()
        session.refresh(entry)

        duration = int((entry.end_time - entry.start_time).total_seconds() / 60)
        return TimeEntryPublic(
            id=entry.id,
            work_log_id=entry.work_log_id,
            start_time=entry.start_time,
            end_time=entry.end_time,
            notes=entry.notes,
            duration_minutes=duration,
            created_at=entry.created_at,
        )

    @staticmethod
    def delete_time_entry(session: Session, entry_id: uuid.UUID) -> None:
        """Delete a time entry."""
        entry = session.get(TimeEntry, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Time entry not found")

        # Check if worklog is paid
        worklog = session.get(WorkLog, entry.work_log_id)
        if worklog.status == WorkLogStatus.PAID:
            raise HTTPException(
                status_code=400, detail="Cannot delete entries from a paid worklog"
            )

        session.delete(entry)
        session.commit()
