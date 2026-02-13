import uuid
from datetime import date
from typing import List, Optional

from fastapi import HTTPException
from datetime import datetime

from sqlmodel import Session, and_, func, select

from app.models import (
    Message,
    TimeEntry,
    TimeEntryPublic,
    WorkLog,
    WorkLogDetail,
    WorkLogPublic,
    WorkLogsPublic,
    WorkLogStatus,
)


class WorkLogService:
    @staticmethod
    def get_worklogs(
        session: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> WorkLogsPublic:
        statement = select(WorkLog)

        if start_date or end_date:
            # Only include worklogs that have UNPAID entries in the date range
            subquery = select(TimeEntry.worklog_id).distinct().where(TimeEntry.is_paid == False)  # noqa: E712
            if start_date:
                subquery = subquery.where(TimeEntry.date >= start_date)
            if end_date:
                subquery = subquery.where(TimeEntry.date <= end_date)
            statement = statement.where(WorkLog.id.in_(subquery))

        worklogs = session.exec(statement.offset(skip).limit(limit)).all()
        count_statement = select(func.count()).select_from(statement.subquery())
        count = session.exec(count_statement).one()

        results = []
        for wl in worklogs:
            # Filter entries for this calculation if a date range is active
            relevant_entries = wl.time_entries
            if start_date or end_date:
                relevant_entries = [
                    te for te in wl.time_entries
                    if (not start_date or te.date >= start_date) and
                       (not end_date or te.date <= end_date)
                ]
            
            # Total eligible to be paid (only unpaid entries)
            total = sum(te.hours * te.hourly_rate for te in relevant_entries if not te.is_paid)
            display_id = f"F{int(wl.freelancer_id.hex[:4], 16) % 100000:05d}"
            
            results.append(
                WorkLogPublic(
                    id=wl.id,
                    task_name=wl.task_name,
                    status=wl.status,
                    freelancer_uuid=wl.freelancer_id,
                    freelancer_id=display_id,
                    freelancer_name=wl.freelancer.full_name or "Unknown Freelancer",
                    total_earned=total,
                )
            )

        return WorkLogsPublic(data=results, count=count)

    @staticmethod
    def get_worklog(
        session: Session, 
        wl_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> WorkLogDetail:
        wl = session.get(WorkLog, wl_id)
        if not wl:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        # Filter entries for the detail view and total calculation
        relevant_entries = wl.time_entries
        if start_date or end_date:
            relevant_entries = [
                te for te in wl.time_entries
                if (not start_date or te.date >= start_date) and
                   (not end_date or te.date <= end_date)
            ]

        total = sum(te.hours * te.hourly_rate for te in relevant_entries)
        display_id = f"F{int(wl.freelancer_id.hex[:4], 16) % 100000:05d}"
        
        entries = [
            TimeEntryPublic(
                id=te.id,
                worklog_id=te.worklog_id,
                date=te.date,
                hours=te.hours,
                hourly_rate=te.hourly_rate,
                description=te.description,
                is_paid=te.is_paid,
                paid_at=te.paid_at,
            )
            for te in relevant_entries
        ]

        return WorkLogDetail(
            id=wl.id,
            task_name=wl.task_name,
            status=wl.status,
            freelancer_uuid=wl.freelancer_id,
            freelancer_id=display_id,
            freelancer_name=wl.freelancer.full_name or "Unknown Freelancer",
            total_earned=total,
            time_entries=entries,
        )

    @staticmethod
    def process_payments(
        session: Session,
        worklog_ids: List[uuid.UUID],
        time_entry_ids: List[uuid.UUID],
        excluded_freelancer_ids: List[uuid.UUID],
    ) -> Message:
        if not worklog_ids and not time_entry_ids:
            return Message(message="No worklogs provided")

        now = datetime.utcnow()

        if time_entry_ids:
            te_stmt = select(TimeEntry).where(TimeEntry.id.in_(time_entry_ids))
            tes = session.exec(te_stmt).all()

            paid = 0
            wls_to_check: set[uuid.UUID] = set()
            for te in tes:
                wl = te.worklog
                if excluded_freelancer_ids and wl.freelancer_id in excluded_freelancer_ids:
                    continue
                if te.is_paid:
                    continue
                te.is_paid = True
                te.paid_at = now
                session.add(te)
                wls_to_check.add(te.worklog_id)
                paid += 1

            for wl_id in wls_to_check:
                wl = session.get(WorkLog, wl_id)
                if not wl:
                    continue
                if all(t.is_paid for t in wl.time_entries):
                    wl.status = WorkLogStatus.PAID
                else:
                    wl.status = WorkLogStatus.PENDING
                session.add(wl)

            session.commit()
            return Message(message=f"Successfully processed payments for {paid} time entries")

        # Fallback: pay all unpaid time entries for selected worklogs
        wl_stmt = select(WorkLog).where(WorkLog.id.in_(worklog_ids))
        if excluded_freelancer_ids:
            wl_stmt = wl_stmt.where(WorkLog.freelancer_id.not_in(excluded_freelancer_ids))
        wls = session.exec(wl_stmt).all()

        paid = 0
        for wl in wls:
            for te in wl.time_entries:
                if te.is_paid:
                    continue
                te.is_paid = True
                te.paid_at = now
                session.add(te)
                paid += 1
            wl.status = WorkLogStatus.PAID
            session.add(wl)

        session.commit()
        return Message(message=f"Successfully processed payments for {len(wls)} worklogs ({paid} entries)")
