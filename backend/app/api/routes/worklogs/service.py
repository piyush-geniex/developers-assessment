from __future__ import annotations

import uuid
from datetime import date, datetime

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    TimeEntry,
    TimeEntryPublic,
    TimeEntryCreate,
    Worklog,
    WorklogCreate,
    WorklogDetail,
    WorklogsPublic,
    WorklogSummary,
    PaymentBatch,
    PaymentBatchCreate,
    PaymentBatchPublic,
)


class WorklogService:
    @staticmethod
    def create_worklog(session: Session, body: WorklogCreate) -> Worklog:
        wl = Worklog.model_validate(body)
        session.add(wl)
        session.commit()
        session.refresh(wl)
        return wl

    @staticmethod
    def create_time_entry(
        session: Session, worklog_id: uuid.UUID, body: TimeEntryCreate
    ) -> TimeEntryPublic:
        wl = session.get(Worklog, worklog_id)
        if not wl:
            raise HTTPException(status_code=404, detail="Worklog not found")

        te = TimeEntry.model_validate(body, update={"worklog_id": worklog_id})
        session.add(te)
        session.commit()
        session.refresh(te)

        amount = WorklogService._calculate_entry_amount(te)
        return TimeEntryPublic(
            id=te.id,
            start_time=te.start_time,
            end_time=te.end_time,
            rate_per_hour=te.rate_per_hour,
            notes=te.notes,
            amount=amount,
        )

    @staticmethod
    def _calculate_entry_amount(entry: TimeEntry) -> float:
        duration = entry.end_time - entry.start_time
        hours = duration.total_seconds() / 3600
        return hours * entry.rate_per_hour

    @staticmethod
    def _build_summary(session: Session, worklog: Worklog) -> WorklogSummary:
        entries_statement = select(TimeEntry).where(TimeEntry.worklog_id == worklog.id)
        entries = session.exec(entries_statement).all()
        if not entries:
            return WorklogSummary(
                id=worklog.id,
                task_name=worklog.task_name,
                freelancer_id=worklog.freelancer_id,
                status=worklog.status,
                total_amount=0.0,
                first_entry_at=None,
                last_entry_at=None,
            )

        amounts: list[float] = []
        first_at: datetime | None = None
        last_at: datetime | None = None

        for entry in entries:
            amount = WorklogService._calculate_entry_amount(entry)
            amounts.append(amount)
            if first_at is None or entry.start_time < first_at:
                first_at = entry.start_time
            if last_at is None or entry.end_time > last_at:
                last_at = entry.end_time

        return WorklogSummary(
            id=worklog.id,
            task_name=worklog.task_name,
            freelancer_id=worklog.freelancer_id,
            status=worklog.status,
            total_amount=sum(amounts),
            first_entry_at=first_at,
            last_entry_at=last_at,
        )

    @staticmethod
    def list_worklogs(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        from_date: date | None = None,
        to_date: date | None = None,
        freelancer_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> WorklogsPublic:
        statement = select(Worklog)

        if from_date is not None:
            statement = statement.where(Worklog.created_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date is not None:
            statement = statement.where(Worklog.created_at <= datetime.combine(to_date, datetime.max.time()))
        if freelancer_id is not None:
            statement = statement.where(Worklog.freelancer_id == freelancer_id)
        if status is not None:
            statement = statement.where(Worklog.status == status)

        count_statement = select(func.count()).select_from(statement.subquery())
        count = session.exec(count_statement).one()

        statement = statement.offset(skip).limit(limit)
        worklogs = session.exec(statement).all()

        summaries = [WorklogService._build_summary(session, wl) for wl in worklogs]
        return WorklogsPublic(data=summaries, count=count)

    @staticmethod
    def get_worklog_detail(session: Session, worklog_id: uuid.UUID) -> WorklogDetail:
        worklog = session.get(Worklog, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="Worklog not found")

        entries_statement = select(TimeEntry).where(TimeEntry.worklog_id == worklog_id)
        entries = session.exec(entries_statement).all()

        public_entries: list[TimeEntryPublic] = []
        total_amount = 0.0
        for entry in entries:
            amount = WorklogService._calculate_entry_amount(entry)
            total_amount += amount
            public_entries.append(
                TimeEntryPublic(
                    id=entry.id,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                    rate_per_hour=entry.rate_per_hour,
                    notes=entry.notes,
                    amount=amount,
                )
            )

        return WorklogDetail(
            id=worklog.id,
            task_name=worklog.task_name,
            freelancer_id=worklog.freelancer_id,
            status=worklog.status,
            total_amount=total_amount,
            entries=public_entries,
        )

    @staticmethod
    def payment_preview(session: Session, body: PaymentBatchCreate) -> PaymentBatchPublic:
        stmt = select(Worklog)

        # Date range on created_at
        stmt = stmt.where(
            Worklog.created_at >= datetime.combine(body.from_date, datetime.min.time())
        ).where(
            Worklog.created_at <= datetime.combine(body.to_date, datetime.max.time())
        )

        if body.worklog_ids:
            stmt = stmt.where(Worklog.id.in_(body.worklog_ids))
        if body.exclude_worklog_ids:
            stmt = stmt.where(Worklog.id.notin_(body.exclude_worklog_ids))
        if body.exclude_freelancer_ids:
            stmt = stmt.where(Worklog.freelancer_id.notin_(body.exclude_freelancer_ids))

        wls = session.exec(stmt).all()

        w_summaries = [WorklogService._build_summary(session, wl) for wl in wls]
        total = sum(w.total_amount for w in w_summaries)

        return PaymentBatchPublic(
            id=uuid.uuid4(),
            from_date=body.from_date,
            to_date=body.to_date,
            total_amount=total,
            worklogs=w_summaries,
        )

    @staticmethod
    def create_payment_batch(session: Session, body: PaymentBatchCreate) -> PaymentBatchPublic:
        preview = WorklogService.payment_preview(session, body)

        ids_str = ",".join(str(w.id) for w in preview.worklogs)
        pb = PaymentBatch(
            id=preview.id,
            from_date=preview.from_date,
            to_date=preview.to_date,
            total_amount=preview.total_amount,
            worklog_ids=ids_str,
        )
        session.add(pb)
        session.commit()
        session.refresh(pb)

        return preview
