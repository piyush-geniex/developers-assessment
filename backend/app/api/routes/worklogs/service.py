import uuid
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, func, select
from sqlalchemy import and_

from app.models import (
    Remittance,
    RemittanceStatus,
    Task,
    TimeEntry,
    User,
    WorkLog,
    WorkLogDetail,
    WorkLogListItem,
    WorkLogsPublic,
    TimeEntryPublic,
    WorkLogRemittanceFilter,
)


class WorkLogService:
    @staticmethod
    def _work_log_amount_cents(session: Session, work_log_id: uuid.UUID) -> int:
        result = session.exec(
            select(func.coalesce(func.sum(TimeEntry.amount_cents), 0)).where(
                TimeEntry.work_log_id == work_log_id
            )
        ).one()
        return result or 0

    @staticmethod
    def list_worklogs(
        session: Session,
        current_user: Any,
        skip: int = 0,
        limit: int = 100,
        date_from: str | None = None,
        date_to: str | None = None,
        remittance_status: WorkLogRemittanceFilter | None = None,
    ) -> WorkLogsPublic:
        """List worklogs with optional date range and remittance status filter."""
        statement = (
            select(WorkLog)
            .join(Task, WorkLog.task_id == Task.id)
            .join(User, WorkLog.user_id == User.id)
        )
        count_statement = (
            select(func.count())
            .select_from(WorkLog)
            .join(Task, WorkLog.task_id == Task.id)
            .join(User, WorkLog.user_id == User.id)
        )

        if date_from is not None or date_to is not None:
            date_conds = [TimeEntry.work_log_id == WorkLog.id]
            if date_from:
                date_conds.append(TimeEntry.entry_date >= date_from)
            if date_to:
                date_conds.append(TimeEntry.entry_date <= date_to)
            date_filter = select(1).where(and_(*date_conds)).exists()
            statement = statement.where(date_filter)
            count_statement = count_statement.where(date_filter)

        if remittance_status == WorkLogRemittanceFilter.REMITTED:
            statement = statement.where(WorkLog.remittance_id.isnot(None))
            count_statement = count_statement.where(WorkLog.remittance_id.isnot(None))
        elif remittance_status == WorkLogRemittanceFilter.UNREMITTED:
            statement = statement.where(WorkLog.remittance_id.is_(None))
            count_statement = count_statement.where(WorkLog.remittance_id.is_(None))

        count = session.exec(count_statement).one()
        work_logs = session.exec(statement.offset(skip).limit(limit)).all()

        items: list[WorkLogListItem] = []
        for wl in work_logs:
            wl = session.get(WorkLog, wl.id)
            if not wl or not wl.task or not wl.user:
                continue
            amount = WorkLogService._work_log_amount_cents(session, wl.id)
            remittance = session.get(Remittance, wl.remittance_id) if wl.remittance_id else None
            items.append(
                WorkLogListItem(
                    id=wl.id,
                    task_id=wl.task_id,
                    task_title=wl.task.title,
                    user_id=wl.user_id,
                    user_email=wl.user.email,
                    user_full_name=wl.user.full_name,
                    amount_cents=amount,
                    remittance_id=wl.remittance_id,
                    remittance_status=remittance.status if remittance else None,
                )
            )

        return WorkLogsPublic(data=items, count=count)

    @staticmethod
    def get_worklog(
        session: Session, current_user: Any, work_log_id: uuid.UUID
    ) -> WorkLogDetail:
        """Get worklog by ID with time entries."""
        work_log = session.get(WorkLog, work_log_id)
        if not work_log:
            raise HTTPException(status_code=404, detail="Work log not found")
        session.refresh(work_log)  # load task, user, time_entries
        if not work_log.task or not work_log.user:
            raise HTTPException(status_code=404, detail="Work log not found")
        amount = WorkLogService._work_log_amount_cents(session, work_log.id)
        remittance = (
            session.get(Remittance, work_log.remittance_id)
            if work_log.remittance_id
            else None
        )
        time_entries = [
            TimeEntryPublic(
                id=te.id,
                work_log_id=te.work_log_id,
                entry_date=te.entry_date,
                duration_minutes=te.duration_minutes,
                amount_cents=te.amount_cents,
                description=te.description,
            )
            for te in work_log.time_entries
        ]
        return WorkLogDetail(
            id=work_log.id,
            task_id=work_log.task_id,
            task_title=work_log.task.title,
            user_id=work_log.user_id,
            user_email=work_log.user.email,
            user_full_name=work_log.user.full_name,
            amount_cents=amount,
            remittance_id=work_log.remittance_id,
            remittance_status=remittance.status if remittance else None,
            time_entries=sorted(time_entries, key=lambda e: e.entry_date),
        )
