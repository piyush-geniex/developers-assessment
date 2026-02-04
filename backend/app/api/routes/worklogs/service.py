import uuid
from datetime import date, datetime
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    TimeEntry,
    TimeEntryCreate,
    TimeEntryPublic,
    TimeEntriesPublic,
    TimeEntryUpdate,
    WorkLog,
    WorkLogCreate,
    WorkLogPublic,
    WorkLogsPublic,
    WorkLogUpdate,
    Payment,
    PaymentCreate,
    PaymentPublic,
    PaymentsPublic,
    PaymentUpdate,
    PaymentWorkLog,
    Message,
)


class WorkLogService:
    @staticmethod
    def get_worklogs(
        session: Session, current_user: Any, skip: int = 0, limit: int = 100
    ) -> WorkLogsPublic:
        """
        Retrieve worklogs.
        """
        count_statement = select(func.count()).select_from(WorkLog)
        count = session.exec(count_statement).one()
        statement = select(WorkLog).offset(skip).limit(limit)
        worklogs = session.exec(statement).all()
        return WorkLogsPublic(data=worklogs, count=count)

    @staticmethod
    def get_worklog(session: Session, current_user: Any, worklog_id: uuid.UUID) -> Any:
        """
        Get worklog by ID with time entries.
        """
        wl = session.get(WorkLog, worklog_id)
        if not wl:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        te_stmt = select(TimeEntry).where(TimeEntry.worklog_id == worklog_id)
        tes = session.exec(te_stmt).all()

        return {"worklog": wl, "time_entries": tes}

    @staticmethod
    def create_worklog(
        session: Session, current_user: Any, worklog_in: WorkLogCreate
    ) -> WorkLogPublic:
        """
        Create new worklog.
        """
        wl = WorkLog(
            task_name=worklog_in.task_name,
            freelancer_id=worklog_in.freelancer_id,
            hourly_rate=worklog_in.hourly_rate,
            total_hours=0.0,
            total_amount=0.0,
            status="PENDING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(wl)
        session.commit()
        session.refresh(wl)
        return wl

    @staticmethod
    def update_worklog(
        session: Session, current_user: Any, worklog_id: uuid.UUID, worklog_in: WorkLogUpdate
    ) -> WorkLogPublic:
        """
        Update a worklog.
        """
        wl = session.get(WorkLog, worklog_id)
        if not wl:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        upd = worklog_in.model_dump(exclude_unset=True)
        wl.sqlmodel_update(upd)
        wl.updated_at = datetime.utcnow()
        session.add(wl)
        session.commit()
        session.refresh(wl)
        return wl

    @staticmethod
    def delete_worklog(session: Session, current_user: Any, worklog_id: uuid.UUID) -> Message:
        """
        Delete a worklog.
        """
        wl = session.get(WorkLog, worklog_id)
        if not wl:
            raise HTTPException(status_code=404, detail="WorkLog not found")
        session.delete(wl)
        session.commit()
        return Message(message="WorkLog deleted successfully")

    @staticmethod
    def get_worklogs_by_date_range(
        session: Session, current_user: Any, date_from: date, date_to: date
    ) -> Any:
        """
        Get worklogs filtered by date range of time entries.
        """
        te_stmt = select(TimeEntry).where(
            TimeEntry.date >= date_from,
            TimeEntry.date <= date_to
        )
        tes = session.exec(te_stmt).all()

        wl_ids = list(set([te.worklog_id for te in tes]))

        wls = []
        for wl_id in wl_ids:
            wl = session.get(WorkLog, wl_id)
            if wl:
                wls.append(wl)

        return {"worklogs": wls, "count": len(wls)}

    @staticmethod
    def exclude_worklog(
        session: Session, current_user: Any, worklog_id: uuid.UUID
    ) -> WorkLogPublic:
        """
        Exclude a worklog from payment.
        """
        wl = session.get(WorkLog, worklog_id)
        if not wl:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        wl.status = "EXCLUDED"
        wl.updated_at = datetime.utcnow()
        session.add(wl)
        session.commit()
        session.refresh(wl)
        return wl


class TimeEntryService:
    @staticmethod
    def get_time_entries(
        session: Session, current_user: Any, worklog_id: uuid.UUID
    ) -> TimeEntriesPublic:
        """
        Get time entries for a worklog.
        """
        stmt = select(TimeEntry).where(TimeEntry.worklog_id == worklog_id)
        tes = session.exec(stmt).all()
        return TimeEntriesPublic(data=tes, count=len(tes))

    @staticmethod
    def create_time_entry(
        session: Session, current_user: Any, time_entry_in: TimeEntryCreate
    ) -> TimeEntryPublic:
        """
        Create new time entry.
        """
        te = TimeEntry(
            worklog_id=time_entry_in.worklog_id,
            description=time_entry_in.description,
            hours=time_entry_in.hours,
            date=time_entry_in.date,
            created_at=datetime.utcnow(),
        )
        session.add(te)
        session.commit()

        wl = session.get(WorkLog, time_entry_in.worklog_id)
        if wl:
            stmt = select(TimeEntry).where(TimeEntry.worklog_id == wl.id)
            tes = session.exec(stmt).all()

            th = 0.0
            for t in tes:
                th += t.hours

            wl.total_hours = th
            wl.total_amount = th * wl.hourly_rate
            wl.updated_at = datetime.utcnow()
            session.add(wl)
            session.commit()

        session.refresh(te)
        return te

    @staticmethod
    def update_time_entry(
        session: Session, current_user: Any, time_entry_id: uuid.UUID, time_entry_in: TimeEntryUpdate
    ) -> TimeEntryPublic:
        """
        Update a time entry.
        """
        te = session.get(TimeEntry, time_entry_id)
        if not te:
            raise HTTPException(status_code=404, detail="TimeEntry not found")

        upd = time_entry_in.model_dump(exclude_unset=True)
        te.sqlmodel_update(upd)
        session.add(te)
        session.commit()

        wl = session.get(WorkLog, te.worklog_id)
        if wl:
            stmt = select(TimeEntry).where(TimeEntry.worklog_id == wl.id)
            tes = session.exec(stmt).all()

            th = 0.0
            for t in tes:
                th += t.hours

            wl.total_hours = th
            wl.total_amount = th * wl.hourly_rate
            wl.updated_at = datetime.utcnow()
            session.add(wl)
            session.commit()

        session.refresh(te)
        return te

    @staticmethod
    def delete_time_entry(
        session: Session, current_user: Any, time_entry_id: uuid.UUID
    ) -> Message:
        """
        Delete a time entry.
        """
        te = session.get(TimeEntry, time_entry_id)
        if not te:
            raise HTTPException(status_code=404, detail="TimeEntry not found")

        wl_id = te.worklog_id
        session.delete(te)
        session.commit()

        wl = session.get(WorkLog, wl_id)
        if wl:
            stmt = select(TimeEntry).where(TimeEntry.worklog_id == wl.id)
            tes = session.exec(stmt).all()

            th = 0.0
            for t in tes:
                th += t.hours

            wl.total_hours = th
            wl.total_amount = th * wl.hourly_rate
            wl.updated_at = datetime.utcnow()
            session.add(wl)
            session.commit()

        return Message(message="TimeEntry deleted successfully")


class PaymentService:
    @staticmethod
    def get_payments(
        session: Session, current_user: Any, skip: int = 0, limit: int = 100
    ) -> PaymentsPublic:
        """
        Retrieve payments.
        """
        count_statement = select(func.count()).select_from(Payment)
        count = session.exec(count_statement).one()
        statement = select(Payment).offset(skip).limit(limit)
        payments = session.exec(statement).all()
        return PaymentsPublic(data=payments, count=count)

    @staticmethod
    def create_payment(
        session: Session, current_user: Any, payment_in: PaymentCreate
    ) -> Any:
        """
        Create new payment batch.
        """
        ta = 0.0
        for wl_id in payment_in.worklog_ids:
            wl = session.get(WorkLog, wl_id)
            if wl:
                ta += wl.total_amount

        pmt = Payment(
            batch_name=payment_in.batch_name,
            date_from=payment_in.date_from,
            date_to=payment_in.date_to,
            total_amount=ta,
            status="DRAFT",
            created_by_id=current_user.id,
            created_at=datetime.utcnow(),
        )
        session.add(pmt)
        session.commit()
        session.refresh(pmt)

        for wl_id in payment_in.worklog_ids:
            wl = session.get(WorkLog, wl_id)
            if wl:
                pwl = PaymentWorkLog(
                    payment_id=pmt.id,
                    worklog_id=wl_id,
                    amount=wl.total_amount,
                )
                session.add(pwl)
                session.commit()

        return pmt

    @staticmethod
    def confirm_payment(
        session: Session, current_user: Any, payment_id: uuid.UUID
    ) -> PaymentPublic:
        """
        Confirm payment and mark worklogs as PAID.
        """
        pmt = session.get(Payment, payment_id)
        if not pmt:
            raise HTTPException(status_code=404, detail="Payment not found")

        pmt.status = "CONFIRMED"
        session.add(pmt)
        session.commit()

        stmt = select(PaymentWorkLog).where(PaymentWorkLog.payment_id == payment_id)
        pwls = session.exec(stmt).all()

        for pwl in pwls:
            wl = session.get(WorkLog, pwl.worklog_id)
            if wl:
                wl.status = "PAID"
                wl.updated_at = datetime.utcnow()
                session.add(wl)
                session.commit()

        session.refresh(pmt)
        return pmt
