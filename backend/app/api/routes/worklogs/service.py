import uuid
from datetime import datetime
from sqlmodel import Session, select, func
from fastapi import HTTPException

from app.models import WorkLog, WorkLogPublic, WorkLogsPublic, TimeEntry, User

class WorkLogService:
    @staticmethod
    def get_worklogs(
        session: Session,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        freelancer_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> WorkLogsPublic:
        query = select(WorkLog)
        
        if date_from:
            query = query.where(WorkLog.created_at >= date_from)
        if date_to:
            query = query.where(WorkLog.created_at <= date_to)
        if freelancer_id:
            query = query.where(WorkLog.freelancer_id == freelancer_id)
            
        count_query = select(func.count()).select_from(query.subquery())
        total_count = session.exec(count_query).one()
        
        query = query.offset(skip).limit(limit).order_by(WorkLog.created_at.desc())
        worklogs = session.exec(query).all()
        
        # Calculate totals
        data = []
        for wl in worklogs:
            # We explicitly load time_entries if not lazy loaded, 
            # or rely on relationship. 
            # Since we need to sum, we can do it in python.
            entries = wl.time_entries
            duration = sum([(te.end_time - te.start_time).total_seconds() / 3600 for te in entries], 0.0)
            amount = sum([((te.end_time - te.start_time).total_seconds() / 3600) * te.rate for te in entries], 0.0)
            
            wl_public = WorkLogPublic(
                id=wl.id,
                freelancer_id=wl.freelancer_id,
                task_name=wl.task_name,
                status=wl.status,
                created_at=wl.created_at,
                total_duration_hours=round(duration, 2),
                total_amount=round(amount, 2)
            )
            data.append(wl_public)
            
        return WorkLogsPublic(data=data, count=total_count)

    @staticmethod
    def get_worklog(session: Session, worklog_id: uuid.UUID) -> WorkLog:
        worklog = session.get(WorkLog, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")
        return worklog

    @staticmethod
    def pay_worklogs(session: Session, worklog_ids: list[uuid.UUID]) -> list[WorkLog]:
        query = select(WorkLog).where(WorkLog.id.in_(worklog_ids))
        worklogs = session.exec(query).all()
        
        for wl in worklogs:
            if wl.status == "pending":
                wl.status = "paid"
                session.add(wl)
        
        session.commit()
        # Refresh to get updated status
        for wl in worklogs:
            session.refresh(wl)
            
        return worklogs
