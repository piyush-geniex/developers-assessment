from datetime import date
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
    Item,
    Message,
    PaymentBatch,
    PaymentBatchCreate,
    PaymentBatchPublic,
    TimeEntry,
    TimeEntryPublic,
    User,
    WorkLog,
    WorkLogDetailPublic,
    WorkLogListItemPublic,
    WorkLogsPublic,
)


def _calc_amount(entries: list[TimeEntry]) -> float:
    """Calculate total from time entries."""
    return sum(e.hours * e.rate for e in entries)


def get_worklogs(
    session: Session,
    current_user,
    start_date: date | None,
    end_date: date | None,
    skip: int = 0,
    limit: int = 100,
) -> WorkLogsPublic:
    """List worklogs; admin sees all, others see own. Filter by entry date range."""
    stmt = select(WorkLog).where(WorkLog.payment_batch_id.is_(None))
    if not current_user.is_superuser:
        stmt = stmt.where(WorkLog.user_id == current_user.id)

    wls = list(session.exec(stmt).all())
    results = []

    for wl in wls:
        entries = list(
            session.exec(
                select(TimeEntry).where(TimeEntry.worklog_id == wl.id)
            ).all()
        )
        if start_date or end_date:
            if start_date:
                entries = [e for e in entries if e.entry_date >= start_date]
            if end_date:
                entries = [e for e in entries if e.entry_date <= end_date]
            if not entries:
                continue

        amt = _calc_amount(entries)
        item = session.get(Item, wl.item_id)
        usr = session.get(User, wl.user_id)
        task_title = item.title if item else ""
        freelancer_email = usr.email if usr else ""
        results.append(
            WorkLogListItemPublic(
                id=wl.id,
                item_id=wl.item_id,
                user_id=wl.user_id,
                status=wl.status,
                total_amount=amt,
                created_at=wl.created_at,
                task_title=task_title,
                freelancer_email=freelancer_email,
                payment_batch_id=wl.payment_batch_id,
            )
        )

    total = len(results)
    results = results[skip : skip + limit]
    return WorkLogsPublic(data=results, count=total)


def get_worklog_detail(
    session: Session, current_user, wl_id: UUID
) -> WorkLogDetailPublic:
    """Get single worklog with time entries."""
    wl = session.get(WorkLog, wl_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Worklog not found")
    if not current_user.is_superuser and wl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    entries = list(
        session.exec(select(TimeEntry).where(TimeEntry.worklog_id == wl_id)).all()
    )
    amt = _calc_amount(entries)
    item = session.get(Item, wl.item_id)
    usr = session.get(User, wl.user_id)
    return WorkLogDetailPublic(
        id=wl.id,
        item_id=wl.item_id,
        user_id=wl.user_id,
        status=wl.status,
        total_amount=amt,
        created_at=wl.created_at,
        task_title=item.title if item else "",
        freelancer_email=usr.email if usr else "",
        time_entries=[
            TimeEntryPublic(
                id=e.id,
                worklog_id=e.worklog_id,
                hours=e.hours,
                rate=e.rate,
                entry_date=e.entry_date,
                description=e.description,
                created_at=e.created_at,
            )
            for e in entries
        ],
    )


def create_payment_batch(
    session: Session, current_user, payload: PaymentBatchCreate
) -> PaymentBatchPublic:
    """Create payment batch from selected worklogs."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin only")

    if not payload.worklog_ids:
        raise HTTPException(
            status_code=400, detail="At least one worklog required"
        )

    ttl = 0.0
    for wl_id in payload.worklog_ids:
        try:
            wl = session.get(WorkLog, wl_id)
            if not wl:
                continue
            if wl.payment_batch_id:
                continue
            entries = list(
                session.exec(
                    select(TimeEntry).where(TimeEntry.worklog_id == wl_id)
                ).all()
            )
            amt = _calc_amount(entries)
            ttl += amt
        except Exception:
            continue

    batch = PaymentBatch(total_amount=ttl, status="completed")
    session.add(batch)
    session.commit()
    session.refresh(batch)

    for wl_id in payload.worklog_ids:
        try:
            wl = session.get(WorkLog, wl_id)
            if wl and not wl.payment_batch_id:
                wl.payment_batch_id = batch.id
                wl.status = "paid"
                session.add(wl)
        except Exception:
            continue

    session.commit()

    return PaymentBatchPublic(
        id=batch.id,
        total_amount=batch.total_amount,
        status=batch.status,
        created_at=batch.created_at,
        worklog_count=len(payload.worklog_ids),
    )
