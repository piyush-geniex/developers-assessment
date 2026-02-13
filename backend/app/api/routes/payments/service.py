import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    EligibleTimeEntry,
    Message,
    Payment,
    PaymentBatch,
    PaymentBatchCreate,
    PaymentBatchDetail,
    PaymentBatchPublic,
    PaymentBatchesPublic,
    PaymentBatchStatus,
    PaymentPublic,
    PaymentsPublic,
    Task,
    TimeEntry,
    User,
)


class PaymentService:
    @staticmethod
    def get_batches(session: Session, skip: int = 0, limit: int = 100) -> PaymentBatchesPublic:
        count = session.exec(select(func.count()).select_from(PaymentBatch)).one()
        batches = session.exec(
            select(PaymentBatch).order_by(PaymentBatch.created_at.desc()).offset(skip).limit(limit)
        ).all()
        return PaymentBatchesPublic(
            data=[PaymentBatchPublic.model_validate(b) for b in batches],
            count=count,
        )

    @staticmethod
    def create_batch(
        session: Session, batch_in: PaymentBatchCreate, created_by_id: uuid.UUID
    ) -> PaymentBatchDetail:
        batch = PaymentBatch(
            date_from=batch_in.date_from,
            date_to=batch_in.date_to,
            created_by_id=created_by_id,
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)

        eligible = PaymentService._get_eligible_entries(session, batch)
        return PaymentBatchDetail(
            batch=PaymentBatchPublic.model_validate(batch),
            eligible_entries=eligible,
        )

    @staticmethod
    def get_batch(session: Session, batch_id: uuid.UUID) -> PaymentBatchDetail:
        batch = session.get(PaymentBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Payment batch not found")
        eligible = PaymentService._get_eligible_entries(session, batch)
        return PaymentBatchDetail(
            batch=PaymentBatchPublic.model_validate(batch),
            eligible_entries=eligible,
        )

    @staticmethod
    def confirm_batch(
        session: Session, batch_id: uuid.UUID, selected_entry_ids: list[uuid.UUID]
    ) -> PaymentBatchPublic:
        batch = session.get(PaymentBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Payment batch not found")
        if batch.status == PaymentBatchStatus.CONFIRMED:
            raise HTTPException(status_code=400, detail="Batch already confirmed")

        total = 0.0
        for entry_id in selected_entry_ids:
            entry = session.get(TimeEntry, entry_id)
            if not entry:
                continue
            freelancer = session.get(User, entry.freelancer_id)
            rate = float(freelancer.hourly_rate) if freelancer and freelancer.hourly_rate else 0.0
            start = entry.start_time
            end = entry.end_time
            hours = (end - start).total_seconds() / 3600
            amount = round(hours * rate, 2)

            payment = Payment(
                batch_id=batch.id,
                freelancer_id=entry.freelancer_id,
                time_entry_id=entry.id,
                hours=round(hours, 4),
                hourly_rate=rate,
                amount=amount,
            )
            session.add(payment)
            total += amount

        batch.status = PaymentBatchStatus.CONFIRMED
        batch.total_amount = round(total, 2)
        batch.confirmed_at = datetime.utcnow()
        session.add(batch)
        session.commit()
        session.refresh(batch)
        return PaymentBatchPublic.model_validate(batch)

    @staticmethod
    def delete_batch(session: Session, batch_id: uuid.UUID) -> Message:
        batch = session.get(PaymentBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Payment batch not found")
        if batch.status == PaymentBatchStatus.CONFIRMED:
            raise HTTPException(status_code=400, detail="Cannot delete a confirmed batch")
        session.delete(batch)
        session.commit()
        return Message(message="Payment batch deleted successfully")

    @staticmethod
    def get_batch_payments(session: Session, batch_id: uuid.UUID) -> PaymentsPublic:
        batch = session.get(PaymentBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Payment batch not found")
        payments = session.exec(
            select(Payment).where(Payment.batch_id == batch_id)
        ).all()
        data = []
        for p in payments:
            entry = session.get(TimeEntry, p.time_entry_id)
            task = session.get(Task, entry.task_id) if entry else None
            freelancer = session.get(User, p.freelancer_id)
            data.append(PaymentPublic(
                id=p.id,
                batch_id=p.batch_id,
                freelancer_id=p.freelancer_id,
                freelancer_name=freelancer.full_name if freelancer and freelancer.full_name else "Unknown",
                time_entry_id=p.time_entry_id,
                task_title=task.title if task else "Unknown",
                hours=p.hours,
                hourly_rate=p.hourly_rate,
                amount=p.amount,
                created_at=p.created_at,
            ))
        return PaymentsPublic(data=data, count=len(data))

    @staticmethod
    def _get_eligible_entries(session: Session, batch: PaymentBatch) -> list[EligibleTimeEntry]:
        # Time entries within the date range that have no payment yet
        paid_entry_ids = session.exec(select(Payment.time_entry_id)).all()
        statement = (
            select(TimeEntry)
            .where(TimeEntry.start_time >= batch.date_from)
            .where(TimeEntry.end_time <= batch.date_to)
        )
        if paid_entry_ids:
            statement = statement.where(TimeEntry.id.not_in(paid_entry_ids))

        entries = session.exec(statement).all()
        result = []
        for entry in entries:
            task = session.get(Task, entry.task_id)
            freelancer = session.get(User, entry.freelancer_id)
            rate = float(freelancer.hourly_rate) if freelancer and freelancer.hourly_rate else 0.0
            hours = round((entry.end_time - entry.start_time).total_seconds() / 3600, 4)
            result.append(EligibleTimeEntry(
                time_entry_id=entry.id,
                task_id=entry.task_id,
                task_title=task.title if task else "Unknown",
                freelancer_id=entry.freelancer_id,
                freelancer_name=freelancer.full_name if freelancer and freelancer.full_name else "Unknown",
                start_time=entry.start_time,
                end_time=entry.end_time,
                hours=hours,
                hourly_rate=rate,
                amount=round(hours * rate, 2),
            ))
        return result
