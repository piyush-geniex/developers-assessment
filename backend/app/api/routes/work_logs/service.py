import uuid
from typing import Any, List
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import update
from sqlmodel import Session, func, select, col

from app.models import (
    WorkLogEntry,
    WorkLogEntryCreate,
    WorkLogEntryItem,
    WorkLogEntries,
    WorkLogEntryUpdate,
    Message,
)


class WorkLogService:
    """Service class for work log entry operations."""

    @staticmethod
    def get_all_work_logs(
        session: Session,
        current_user: Any,
        skip: int = 0,
        limit: int = 100,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> WorkLogEntries:
        """
        Retrieve all work log entries across all tasks.
        """
        # Adjust end_time to be at 23:59:59 of that day for inclusive filtering
        if end_time is not None:
            end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # build conditions
        conditions = []
        if start_time is not None:
            conditions.append(WorkLogEntry.start_time >= start_time)
        if end_time is not None:
            conditions.append(WorkLogEntry.end_time <= end_time)

        if current_user.is_superuser:
            count_stmt = select(func.count()).select_from(WorkLogEntry)
            if conditions:
                combined = conditions[0]
                for c in conditions[1:]:
                    combined = combined & c
                count_stmt = count_stmt.where(combined)
            count = session.exec(count_stmt).one()
            stmt = select(WorkLogEntry)
            if conditions:
                stmt = stmt.where(combined)
            stmt = stmt.offset(skip).limit(limit)
            work_logs = session.exec(stmt).all()
        else:
            conditions.append(WorkLogEntry.created_by_id == current_user.id)
            combined = conditions[0]
            for c in conditions[1:]:
                combined = combined & c
            count_stmt = select(func.count()).select_from(WorkLogEntry).where(combined)
            count = session.exec(count_stmt).one()
            stmt = select(WorkLogEntry).where(combined).offset(skip).limit(limit)
            work_logs = session.exec(stmt).all()

        return WorkLogEntries(data=work_logs, count=count)

    @staticmethod
    def get_work_logs(
        session: Session,
        current_user: Any,
        task_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> WorkLogEntries:
        """
        Retrieve work log entries for a task.
        """
        # Adjust end_time to be at 23:59:59 of that day for inclusive filtering
        if end_time is not None:
            end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # build conditions for task
        conditions = [WorkLogEntry.task_id == task_id]
        if start_time is not None:
            conditions.append(WorkLogEntry.start_time >= start_time)
        if end_time is not None:
            conditions.append(WorkLogEntry.end_time <= end_time)
        combined = conditions[0]
        for c in conditions[1:]:
            combined = combined & c

        if current_user.is_superuser:
            count_stmt = select(func.count()).select_from(WorkLogEntry).where(combined)
            count = session.exec(count_stmt).one()
            stmt = select(WorkLogEntry).where(combined).offset(skip).limit(limit)
            work_logs = session.exec(stmt).all()
        else:
            combined = combined & (WorkLogEntry.created_by_id == current_user.id)
            count_stmt = select(func.count()).select_from(WorkLogEntry).where(combined)
            count = session.exec(count_stmt).one()
            stmt = select(WorkLogEntry).where(combined).offset(skip).limit(limit)
            work_logs = session.exec(stmt).all()

        return WorkLogEntries(data=work_logs, count=count)

    @staticmethod
    def get_work_log(
        session: Session, current_user: Any, task_id: uuid.UUID, work_log_id: uuid.UUID
    ) -> WorkLogEntryItem:
        """
        Get work log entry by ID for a specific task.
        """
        work_log = session.get(WorkLogEntry, work_log_id)
        if not work_log:
            raise HTTPException(status_code=404, detail="Work log entry not found")
        if work_log.task_id != task_id:
            raise HTTPException(status_code=404, detail="Work log entry not found for this task")
        if not current_user.is_superuser and (work_log.created_by_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return work_log

    @staticmethod
    def create_work_log(
        session: Session, current_user: Any, task_id: uuid.UUID, work_log_in: WorkLogEntryCreate
    ) -> WorkLogEntryItem:
        """
        Create new work log entry for a task.
        """
        work_log = WorkLogEntry.model_validate(
            work_log_in,
            update={"created_by_id": current_user.id, "task_id": task_id, "created_at": datetime.now(timezone.utc)},
        )
        session.add(work_log)
        session.commit()
        session.refresh(work_log)
        return work_log

    @staticmethod
    def update_work_log(
        session: Session,
        current_user: Any,
        task_id: uuid.UUID,
        work_log_id: uuid.UUID,
        work_log_in: WorkLogEntryUpdate,
    ) -> WorkLogEntryItem:
        """
        Update a work log entry for a task.
        """
        work_log = session.get(WorkLogEntry, work_log_id)
        if not work_log:
            raise HTTPException(status_code=404, detail="Work log entry not found")
        if work_log.task_id != task_id:
            raise HTTPException(status_code=404, detail="Work log entry not found for this task")
        if not current_user.is_superuser and (work_log.created_by_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not enough permissions")

        update_dict = work_log_in.model_dump(exclude_unset=True)
        update_dict["edited_by_id"] = current_user.id
        update_dict["edited_at"] = datetime.now(timezone.utc)

        work_log.sqlmodel_update(update_dict)
    @staticmethod
    def approve_work_log(
        session: Session, current_user: Any, task_id: uuid.UUID, work_log_id: uuid.UUID
    ) -> WorkLogEntryItem:
        """
        Approve a work log entry for a task.
        """
        work_log = session.get(WorkLogEntry, work_log_id)
        if not work_log:
            raise HTTPException(status_code=404, detail="Work log entry not found")
        if work_log.task_id != task_id:
            raise HTTPException(status_code=404, detail="Work log entry not found for this task")

        work_log.approved = True
        work_log.approved_date = datetime.now(timezone.utc)
        work_log.approved_by_id = current_user.id
        work_log.edited_by_id = current_user.id
        work_log.edited_at = datetime.now(timezone.utc)

        session.add(work_log)
        session.commit()
        session.refresh(work_log)
        return work_log

    @staticmethod
    def initiate_payment(
        session: Session, current_user: Any, task_id: uuid.UUID, work_log_id: uuid.UUID
    ) -> WorkLogEntryItem:
        """
        Initiate payment for a work log entry in a task.
        """
        work_log = session.get(WorkLogEntry, work_log_id)
        if not work_log:
            raise HTTPException(status_code=404, detail="Work log entry not found")
        if work_log.task_id != task_id:
            raise HTTPException(status_code=404, detail="Work log entry not found for this task")

        if not work_log.approved:
            raise HTTPException(
                status_code=400, detail="Work log entry must be approved before payment"
            )

        work_log.payment_initiated = True
        work_log.payment_initiated_date = datetime.now(timezone.utc)
        work_log.initiated_by_id = current_user.id
        work_log.edited_by_id = current_user.id
        work_log.edited_at = datetime.now(timezone.utc)

        session.add(work_log)
        session.commit()
        session.refresh(work_log)
        return work_log

    @staticmethod
    def delete_work_log(
        session: Session, current_user: Any, task_id: uuid.UUID, work_log_id: uuid.UUID
    ) -> Message:
        """
        Delete a work log entry for a task.
        """
        work_log = session.get(WorkLogEntry, work_log_id)
        if not work_log:
            raise HTTPException(status_code=404, detail="Work log entry not found")
        if work_log.task_id != task_id:
            raise HTTPException(status_code=404, detail="Work log entry not found for this task")
        if not current_user.is_superuser and (work_log.created_by_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        session.delete(work_log)
        session.commit()
        return Message(message="Work log entry deleted successfully")
