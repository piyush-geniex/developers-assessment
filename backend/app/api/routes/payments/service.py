import logging
import uuid
from datetime import date, datetime, time

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    ConfirmBatchIn,
    EligibleEntry,
    Payment,
    PaymentBatch,
    PaymentBatchCreate,
    PaymentBatchDetail,
    PaymentBatchPublic,
    PaymentBatchesPublic,
    TimeEntry,
    User,
    Worklog,
)

logger = logging.getLogger(__name__)


class PaymentService:
    @staticmethod
    def list_batches(session: Session, skip: int, limit: int) -> PaymentBatchesPublic:
        try:
            count = session.exec(select(func.count()).select_from(PaymentBatch)).one()
            batches = session.exec(
                select(PaymentBatch)
                .order_by(PaymentBatch.created_at.desc())
                .offset(skip)
                .limit(limit)
            ).all()
        except Exception as exc:
            logger.error("Failed to list payment batches: %s", exc)
            return PaymentBatchesPublic(data=[], count=0)

        return PaymentBatchesPublic(
            data=[PaymentService._batch_to_public(b) for b in batches],
            count=count,
        )

    @staticmethod
    def create_batch(
        session: Session, current_user: User, batch_in: PaymentBatchCreate
    ) -> PaymentBatchDetail:
        if batch_in.date_from > batch_in.date_to:
            raise HTTPException(
                status_code=400, detail="date_from must be on or before date_to"
            )

        batch = PaymentBatch(
            date_from=batch_in.date_from,
            date_to=batch_in.date_to,
            status="draft",
            created_by_id=current_user.id,
            created_at=datetime.utcnow(),
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)

        eligible = PaymentService._get_eligible_entries(
            session, batch_in.date_from, batch_in.date_to
        )

        return PaymentBatchDetail(
            **PaymentService._batch_to_public(batch).model_dump(),
            eligible_entries=eligible,
        )

    @staticmethod
    def get_batch(session: Session, batch_id: uuid.UUID) -> PaymentBatchDetail:
        batch = session.get(PaymentBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Payment batch not found")

        if batch.status == "confirmed":
            return PaymentBatchDetail(
                **PaymentService._batch_to_public(batch).model_dump(),
                eligible_entries=[],
                payment_lines=PaymentService._get_payment_lines(session, batch_id),
            )

        eligible = PaymentService._get_eligible_entries(
            session, batch.date_from, batch.date_to
        )

        return PaymentBatchDetail(
            **PaymentService._batch_to_public(batch).model_dump(),
            eligible_entries=eligible,
        )

    @staticmethod
    def confirm_batch(
        session: Session, batch_id: uuid.UUID, confirm_in: ConfirmBatchIn
    ) -> PaymentBatchPublic:
        batch = session.get(PaymentBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Payment batch not found")
        if batch.status != "draft":
            raise HTTPException(
                status_code=409, detail="Only draft batches can be confirmed"
            )

        eligible = PaymentService._get_eligible_entries(
            session, batch.date_from, batch.date_to
        )

        excluded_wl = set(confirm_in.excluded_worklog_ids)
        excluded_fl = set(confirm_in.excluded_freelancer_ids)

        total = 0.0
        for entry in eligible:
            if entry.worklog_id in excluded_wl or entry.freelancer_id in excluded_fl:
                continue
            try:
                payment = Payment(
                    batch_id=batch.id,
                    time_entry_id=entry.time_entry_id,
                    worklog_id=entry.worklog_id,
                    freelancer_id=entry.freelancer_id,
                    hours=entry.hours,
                    hourly_rate=entry.hourly_rate,
                    amount=entry.amount,
                    created_at=datetime.utcnow(),
                )
                session.add(payment)
                session.commit()
                total += entry.amount
            except Exception as exc:
                logger.error(
                    "Failed to create payment for time_entry %s: %s",
                    entry.time_entry_id,
                    exc,
                )
                continue

        batch.status = "confirmed"
        batch.total_amount = round(total, 2)
        batch.confirmed_at = datetime.utcnow()
        session.add(batch)
        session.commit()
        session.refresh(batch)

        return PaymentService._batch_to_public(batch)

    @staticmethod
    def delete_batch(session: Session, batch_id: uuid.UUID) -> None:
        batch = session.get(PaymentBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Payment batch not found")
        if batch.status != "draft":
            raise HTTPException(
                status_code=409, detail="Only draft batches can be deleted"
            )
        session.delete(batch)
        session.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_payment_lines(
        session: Session, batch_id: uuid.UUID
    ) -> list[EligibleEntry]:
        """Return all payment records for a confirmed batch with freelancer/worklog names."""
        stmt = (
            select(Payment, Worklog, User, TimeEntry)
            .join(Worklog, Worklog.id == Payment.worklog_id)
            .join(User, User.id == Payment.freelancer_id)
            .join(TimeEntry, TimeEntry.id == Payment.time_entry_id)
            .where(Payment.batch_id == batch_id)
            .order_by(User.full_name.asc(), Worklog.title.asc())
        )

        try:
            rows = session.execute(stmt).all()
        except Exception as exc:
            logger.error("Failed to fetch payment lines for batch %s: %s", batch_id, exc)
            return []

        return [
            EligibleEntry(
                time_entry_id=row[0].time_entry_id,
                worklog_id=row[1].id,
                worklog_title=row[1].title,
                freelancer_id=row[2].id,
                freelancer_name=row[2].full_name,
                hours=row[0].hours,
                hourly_rate=row[0].hourly_rate,
                amount=row[0].amount,
                start_time=row[3].start_time,
                end_time=row[3].end_time,
            )
            for row in rows
        ]

    @staticmethod
    def _batch_to_public(batch: PaymentBatch) -> PaymentBatchPublic:
        return PaymentBatchPublic(
            id=batch.id,
            date_from=batch.date_from,
            date_to=batch.date_to,
            status=batch.status,
            created_by_id=batch.created_by_id,
            total_amount=batch.total_amount,
            created_at=batch.created_at,
            confirmed_at=batch.confirmed_at,
        )

    @staticmethod
    def _get_eligible_entries(
        session: Session, date_from: date, date_to: date
    ) -> list[EligibleEntry]:
        """
        Return time entries within the date range that are not already
        included in a confirmed payment batch.
        """
        confirmed_entry_ids_stmt = select(Payment.time_entry_id).join(
            PaymentBatch, PaymentBatch.id == Payment.batch_id
        ).where(PaymentBatch.status == "confirmed")

        try:
            confirmed_ids = set(session.exec(confirmed_entry_ids_stmt).all())
        except Exception as exc:
            logger.error("Failed to fetch confirmed entry IDs: %s", exc)
            confirmed_ids = set()

        stmt = (
            select(TimeEntry, Worklog, User)
            .join(Worklog, Worklog.id == TimeEntry.worklog_id)
            .join(User, User.id == Worklog.freelancer_id)
            .where(
                TimeEntry.start_time >= datetime.combine(date_from, time.min),
                TimeEntry.start_time <= datetime.combine(date_to, time.max),
            )
            .order_by(TimeEntry.start_time.asc())
        )

        try:
            rows = session.execute(stmt).all()
        except Exception as exc:
            logger.error("Failed to fetch eligible entries: %s", exc)
            return []

        entries: list[EligibleEntry] = []
        for row in rows:
            te: TimeEntry = row[0]
            wl: Worklog = row[1]
            user: User = row[2]

            if te.id in confirmed_ids:
                continue

            entries.append(
                EligibleEntry(
                    time_entry_id=te.id,
                    worklog_id=wl.id,
                    worklog_title=wl.title,
                    freelancer_id=user.id,
                    freelancer_name=user.full_name,
                    hours=te.hours,
                    hourly_rate=wl.hourly_rate,
                    amount=round(te.hours * wl.hourly_rate, 2),
                    start_time=te.start_time,
                    end_time=te.end_time,
                )
            )

        return entries
