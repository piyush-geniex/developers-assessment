from sqlmodel import func, select
from sqlalchemy.orm import selectinload
from app.api.deps import SessionDep
from app.models import WorkLog, WorkLogPublic, WorkLogsPublic, Message, TimeEntryPublic
import uuid

class WorkLogService:
    @staticmethod
    def get_worklogs(session: SessionDep, skip: int = 0, limit: int = 100) -> WorkLogsPublic:
        query = select(WorkLog).options(
            selectinload(WorkLog.freelancer), 
            selectinload(WorkLog.time_entries)
        ).offset(skip).limit(limit)
        
        db_logs = session.exec(query).all()
        count = session.exec(select(func.count()).select_from(WorkLog)).one()
        
        public_items = []
        for log in db_logs:
            hours_sum = sum(t.hours for t in log.time_entries)
            entries = [
                TimeEntryPublic(date=t.date, hours=t.hours, description=t.description) 
                for t in log.time_entries
            ]

            public_items.append(WorkLogPublic(
                id=log.id,
                task_name=log.task_name,
                hourly_rate=log.hourly_rate,
                status=log.status,
                freelancer_name=log.freelancer.name,
                total_hours=hours_sum,
                total_amount=hours_sum * log.hourly_rate,
                time_entries=entries
            ))
            
        return WorkLogsPublic(data=public_items, count=count)

    @staticmethod
    def pay_worklog(session: SessionDep, id: uuid.UUID) -> Message:
        log = session.get(WorkLog, id)
        if not log:
            return Message(message="WorkLog not found")
        
        log.status = "paid"
        session.add(log)
        session.commit()
        return Message(message="Status updated to paid")