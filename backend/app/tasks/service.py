import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.tasks.models import (
    Dispute,
    DisputeStatus,
    RemittanceStatus,
    Task,
    TimeSegment,
    TimeSegmentStatus,
    WorkLog,
)
from app.tasks.schemas import (
    DisputeCreate,
    TasksPublic,
    TaskUpdate,
    TimeSegmentCreate,
    TimeSegmentUpdate,
    WorkLogCreate,
    WorkLogsPublic,
)


class TaskService:
    @staticmethod
    def create_task(session: Session, task_in: Any, creator_id: uuid.UUID) -> Task:
        task = Task.model_validate(task_in, update={"created_by_id": creator_id})
        session.add(task)
        session.flush()
        session.refresh(task)
        return task

    @staticmethod
    def get_task(session: Session, task_id: uuid.UUID) -> Task:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @staticmethod
    def get_tasks(session: Session, skip: int = 0, limit: int = 100) -> TasksPublic:
        count_statement = select(func.count()).select_from(Task)
        count = session.exec(count_statement).one()
        statement = select(Task).offset(skip).limit(limit)
        tasks = session.exec(statement).all()
        return TasksPublic(data=tasks, count=count)

    @staticmethod
    def update_task(session: Session, task_id: uuid.UUID, task_in: TaskUpdate) -> Task:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        update_data = task_in.model_dump(exclude_unset=True)
        task.sqlmodel_update(update_data)
        session.add(task)
        session.flush()
        session.refresh(task)
        return task

    @staticmethod
    def create_worklog(session: Session, worklog_in: WorkLogCreate) -> WorkLog:
        task = session.get(Task, worklog_in.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        worklog = WorkLog.model_validate(worklog_in)
        session.add(worklog)
        session.flush()
        session.refresh(worklog)
        return worklog

    @staticmethod
    def get_worklog(session: Session, worklog_id: uuid.UUID) -> WorkLog:
        worklog = session.get(WorkLog, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")
        return worklog

    @staticmethod
    def get_worklogs(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        remittance_status: RemittanceStatus | None = None,
    ) -> WorkLogsPublic:
        query = select(WorkLog)
        if remittance_status:
            query = query.where(WorkLog.remittance_status == remittance_status)

        count_statement = select(func.count()).select_from(query.subquery())
        count = session.exec(count_statement).one()

        statement = query.offset(skip).limit(limit)
        worklogs = session.exec(statement).all()
        return WorkLogsPublic(data=worklogs, count=count)

    @staticmethod
    def create_timesegment(
        session: Session, segment_in: TimeSegmentCreate
    ) -> TimeSegment:
        worklog = session.get(WorkLog, segment_in.work_log_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        segment = TimeSegment.model_validate(segment_in)
        # Snapshot current rate
        segment.rate_at_recording = worklog.task.rate_amount

        if worklog.remittance_status == RemittanceStatus.REMITTED:
            worklog.remittance_status = RemittanceStatus.UNREMITTED
            session.add(worklog)

        session.add(segment)
        session.flush()
        session.refresh(segment)
        return segment

    @staticmethod
    def get_timesegment(session: Session, segment_id: uuid.UUID) -> TimeSegment:
        segment = session.get(TimeSegment, segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="TimeSegment not found")
        return segment

    @staticmethod
    def update_timesegment(
        session: Session, segment_id: uuid.UUID, segment_in: TimeSegmentUpdate | dict[str, Any]
    ) -> TimeSegment:
        segment = session.get(TimeSegment, segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="TimeSegment not found")

        if segment.remittance_id:
            # Immutability guard - once remitted, no direct updates
            raise HTTPException(
                status_code=400,
                detail="Cannot update a segment that has already been remitted",
            )

        if isinstance(segment_in, dict):
            update_data = segment_in
        else:
            update_data = segment_in.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(segment, key, value)

        session.add(segment)
        session.flush()
        session.refresh(segment)
        return segment

    @staticmethod
    def dispute_timesegment(session: Session, segment_id: uuid.UUID, reason: str) -> Dispute:
        segment = session.get(TimeSegment, segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="TimeSegment not found")

        dispute = Dispute(
            time_segment_id=segment_id, reason=reason, status=DisputeStatus.OPEN
        )
        segment.status = TimeSegmentStatus.DISPUTED

        session.add(dispute)
        session.add(segment)
        session.flush()
        session.refresh(dispute)
        return dispute

    @staticmethod
    def resolve_dispute(
        session: Session, dispute_id: uuid.UUID, resolution: str, approved: bool
    ) -> Dispute:
        dispute = session.get(Dispute, dispute_id)
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")

        dispute.resolution_notes = resolution
        dispute.status = DisputeStatus.RESOLVED if approved else DisputeStatus.REJECTED
        dispute.resolved_at = datetime.now(timezone.utc)  # Use UTC timezone

        segment = dispute.time_segment
        if approved:
            segment.status = TimeSegmentStatus.APPROVED
        else:
            segment.status = TimeSegmentStatus.REJECTED

        session.add(dispute)
        session.add(segment)
        session.flush()
        session.refresh(dispute)
        return dispute

    @staticmethod
    def get_all_worklogs_with_amounts(
        session: Session,
        remittance_status: RemittanceStatus | None = None,
        include_accrued: bool = False,
    ) -> list[dict]:
        """
        Custom method to get worklogs with calculated amounts.
        """
        query = select(WorkLog)
        if remittance_status:
            query = query.where(WorkLog.remittance_status == remittance_status)

        worklogs = session.exec(query).all()

        results = []
        for wl in worklogs:
            total_amount = Decimal(0)
            accrued_amount = Decimal(0)

            for segment in wl.time_segments:
                rate = segment.rate_at_recording or wl.task.rate_amount
                amount = segment.duration_hours * rate

                if segment.status == TimeSegmentStatus.SETTLED:
                    total_amount += amount
                elif include_accrued and segment.status in [
                    TimeSegmentStatus.APPROVED,
                    TimeSegmentStatus.PENDING,
                ]:
                    accrued_amount += amount

            res = {
                "id": wl.id,
                "worker_id": wl.worker_id,
                "task_id": wl.task_id,
                "remittance_status": wl.remittance_status,
                "amount": total_amount,
                "created_at": wl.created_at,
                "updated_at": wl.updated_at,
            }
            if include_accrued:
                res["accrued_amount"] = accrued_amount

            results.append(res)

        return results