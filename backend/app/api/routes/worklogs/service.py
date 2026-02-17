import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    Payment,
    PaymentBatch,
    PaymentBatchCreate,
    PaymentBatchDetail,
    PaymentBatchPublic,
    PaymentPublic,
    Task,
    TaskCreate,
    TaskPublic,
    TimeEntry,
    TimeEntryCreate,
    TimeEntryPublic,
    User,
    UserPublic,
    WorkLog,
    WorkLogCreate,
    WorkLogDetail,
    WorkLogPublic,
    WorkLogsPublic,
)


class WorkLogService:
    @staticmethod
    def get_worklogs(
        session: Session,
        current_user: Any,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> WorkLogsPublic:
        """
        Retrieve worklogs with earnings calculation.
        """
        statement = select(WorkLog)
        if start_date:
            statement = statement.where(WorkLog.created_at >= start_date)
        if end_date:
            statement = statement.where(WorkLog.created_at <= end_date)

        if not current_user.is_superuser:
            statement = statement.where(WorkLog.freelancer_id == current_user.id)

        count_statement = select(func.count()).select_from(statement.subquery())
        count = session.exec(count_statement).one()

        statement = statement.offset(skip).limit(limit)
        worklogs = session.exec(statement).all()

        wl_list = []
        for wl in worklogs:
            te_list = session.exec(
                select(TimeEntry).where(TimeEntry.worklog_id == wl.id)
            ).all()
            total = sum(te.hours * te.rate for te in te_list)

            task = session.get(Task, wl.task_id)
            freelancer = session.get(User, wl.freelancer_id)

            wl_pub = WorkLogPublic(
                id=wl.id,
                task_id=wl.task_id,
                freelancer_id=wl.freelancer_id,
                status=wl.status,
                created_at=wl.created_at,
                updated_at=wl.updated_at,
                total_earnings=total,
                task=TaskPublic(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    created_at=task.created_at,
                )
                if task
                else None,
                freelancer=UserPublic(
                    id=freelancer.id,
                    email=freelancer.email,
                    is_active=freelancer.is_active,
                    is_superuser=freelancer.is_superuser,
                    full_name=freelancer.full_name,
                ) if freelancer else None,
            )
            wl_list.append(wl_pub)

        return WorkLogsPublic(data=wl_list, count=count)

    @staticmethod
    def get_worklog(
        session: Session, current_user: Any, worklog_id: uuid.UUID
    ) -> WorkLogDetail:
        """
        Get worklog by ID with time entries.
        """
        wl = session.get(WorkLog, worklog_id)
        if not wl:
            raise HTTPException(status_code=404, detail="Worklog not found")
        if not current_user.is_superuser and (wl.freelancer_id != current_user.id):
            raise HTTPException(status_code=400, detail="Not enough permissions")

        te_list = session.exec(
            select(TimeEntry).where(TimeEntry.worklog_id == worklog_id)
        ).all()

        te_pub_list = []
        for te in te_list:
            te_pub = TimeEntryPublic(
                id=te.id,
                worklog_id=te.worklog_id,
                hours=te.hours,
                rate=te.rate,
                description=te.description,
                entry_date=te.entry_date,
                created_at=te.created_at,
                earnings=te.hours * te.rate,
            )
            te_pub_list.append(te_pub)

        total = sum(te.hours * te.rate for te in te_list)

        task = session.get(Task, wl.task_id)
        freelancer = session.get(User, wl.freelancer_id)

        return WorkLogDetail(
            id=wl.id,
            task_id=wl.task_id,
            freelancer_id=wl.freelancer_id,
            status=wl.status,
            created_at=wl.created_at,
            updated_at=wl.updated_at,
            total_earnings=total,
            task=TaskPublic(
                id=task.id, title=task.title, description=task.description, created_at=task.created_at
            ) if task else None,
            freelancer=UserPublic(
                id=freelancer.id,
                email=freelancer.email,
                is_active=freelancer.is_active,
                is_superuser=freelancer.is_superuser,
                full_name=freelancer.full_name,
            ) if freelancer else None,
            time_entries=te_pub_list,
        )

    @staticmethod
    def create_payment_batch(
        session: Session,
        current_user: Any,
        batch_in: PaymentBatchCreate,
    ) -> PaymentBatchDetail:
        """
        Create payment batch with exclusions.
        """
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        excluded_wl_ids = set(batch_in.excluded_worklog_ids)
        excluded_freelancer_ids = set(batch_in.excluded_freelancer_ids)

        wl_statement = select(WorkLog).where(
            WorkLog.created_at >= batch_in.start_date,
            WorkLog.created_at <= batch_in.end_date,
        )

        eligible_wls = session.exec(wl_statement).all()
        filtered_wls = [
            wl
            for wl in eligible_wls
            if wl.id not in excluded_wl_ids
            and wl.freelancer_id not in excluded_freelancer_ids
        ]

        batch = PaymentBatch(
            status="PENDING",
            start_date=batch_in.start_date,
            end_date=batch_in.end_date,
            notes=batch_in.notes,
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)

        total_amt = 0.0
        payment_list = []

        for wl in filtered_wls:
            te_list = session.exec(
                select(TimeEntry).where(TimeEntry.worklog_id == wl.id)
            ).all()
            wl_total = sum(te.hours * te.rate for te in te_list)

            if wl_total > 0:
                pmt = Payment(
                    worklog_id=wl.id,
                    payment_batch_id=batch.id,
                    amount=wl_total,
                    status="PENDING",
                )
                session.add(pmt)
                session.commit()
                session.refresh(pmt)
                payment_list.append(pmt)
                total_amt += wl_total

        batch.total_amount = total_amt
        session.add(batch)
        session.commit()
        session.refresh(batch)

        pmt_pub_list = []
        for pmt in payment_list:
            wl = session.get(WorkLog, pmt.worklog_id)
            task = session.get(Task, wl.task_id) if wl else None
            freelancer = session.get(User, wl.freelancer_id) if wl else None

            pmt_pub = PaymentPublic(
                id=pmt.id,
                worklog_id=pmt.worklog_id,
                payment_batch_id=pmt.payment_batch_id,
                amount=pmt.amount,
                status=pmt.status,
                created_at=pmt.created_at,
                processed_at=pmt.processed_at,
                worklog=WorkLogPublic(
                    id=wl.id,
                    task_id=wl.task_id,
                    freelancer_id=wl.freelancer_id,
                    status=wl.status,
                    created_at=wl.created_at,
                    updated_at=wl.updated_at,
                    total_earnings=pmt.amount,
                    task=TaskPublic(
                        id=task.id,
                        title=task.title,
                        description=task.description,
                        created_at=task.created_at,
                    ) if task else None,
                    freelancer=UserPublic(
                        id=freelancer.id,
                        email=freelancer.email,
                        is_active=freelancer.is_active,
                        is_superuser=freelancer.is_superuser,
                        full_name=freelancer.full_name,
                    ) if freelancer else None,
                ) if wl else None,
            )
            pmt_pub_list.append(pmt_pub)

        return PaymentBatchDetail(
            id=batch.id,
            status=batch.status,
            start_date=batch.start_date,
            end_date=batch.end_date,
            notes=batch.notes,
            created_at=batch.created_at,
            processed_at=batch.processed_at,
            total_amount=batch.total_amount,
            payment_count=len(pmt_pub_list),
            payments=pmt_pub_list,
        )

    @staticmethod
    def confirm_payment_batch(
        session: Session, current_user: Any, batch_id: uuid.UUID
    ) -> PaymentBatchPublic:
        """
        Confirm and process payment batch.
        """
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        batch = session.get(PaymentBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Payment batch not found")

        if batch.status != "PENDING":
            raise HTTPException(
                status_code=400, detail="Payment batch already processed"
            )

        pmt_list = session.exec(
            select(Payment).where(Payment.payment_batch_id == batch_id)
        ).all()

        now = datetime.utcnow()
        for pmt in pmt_list:
            pmt.status = "COMPLETED"
            pmt.processed_at = now
            session.add(pmt)
            session.commit()

        batch.status = "COMPLETED"
        batch.processed_at = now
        session.add(batch)
        session.commit()
        session.refresh(batch)

        pmt_count = len(pmt_list)

        return PaymentBatchPublic(
            id=batch.id,
            status=batch.status,
            start_date=batch.start_date,
            end_date=batch.end_date,
            notes=batch.notes,
            created_at=batch.created_at,
            processed_at=batch.processed_at,
            total_amount=batch.total_amount,
            payment_count=pmt_count,
        )

    @staticmethod
    def create_task(
        session: Session, current_user: Any, task_in: TaskCreate
    ) -> TaskPublic:
        """
        Create a new task.
        """
        task = Task.model_validate(task_in)
        session.add(task)
        session.commit()
        session.refresh(task)
        return TaskPublic(
            id=task.id,
            title=task.title,
            description=task.description,
            created_at=task.created_at,
        )

    @staticmethod
    def create_worklog(
        session: Session, current_user: Any, worklog_in: WorkLogCreate
    ) -> WorkLogPublic:
        """
        Create a new worklog.
        """
        task = session.get(Task, worklog_in.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        freelancer = session.get(User, worklog_in.freelancer_id)
        if not freelancer:
            raise HTTPException(status_code=404, detail="Freelancer not found")

        if not current_user.is_superuser and (
            worklog_in.freelancer_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Not enough permissions")

        wl = WorkLog(
            task_id=worklog_in.task_id,
            freelancer_id=worklog_in.freelancer_id,
            status=worklog_in.status,
        )
        session.add(wl)
        session.commit()
        session.refresh(wl)

        return WorkLogPublic(
            id=wl.id,
            task_id=wl.task_id,
            freelancer_id=wl.freelancer_id,
            status=wl.status,
            created_at=wl.created_at,
            updated_at=wl.updated_at,
            total_earnings=0.0,
            task=TaskPublic(
                id=task.id,
                title=task.title,
                description=task.description,
                created_at=task.created_at,
            ),
            freelancer=UserPublic(
                id=freelancer.id,
                email=freelancer.email,
                is_active=freelancer.is_active,
                is_superuser=freelancer.is_superuser,
                full_name=freelancer.full_name,
            ),
        )

    @staticmethod
    def create_time_entry(
        session: Session, current_user: Any, time_entry_in: TimeEntryCreate
    ) -> TimeEntryPublic:
        """
        Create a new time entry.
        """
        wl = session.get(WorkLog, time_entry_in.worklog_id)
        if not wl:
            raise HTTPException(status_code=404, detail="Worklog not found")

        if not current_user.is_superuser and (wl.freelancer_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not enough permissions")

        te = TimeEntry(
            worklog_id=time_entry_in.worklog_id,
            hours=time_entry_in.hours,
            rate=time_entry_in.rate,
            description=time_entry_in.description,
            entry_date=time_entry_in.entry_date,
        )
        session.add(te)
        session.commit()
        session.refresh(te)

        wl.updated_at = datetime.utcnow()
        session.add(wl)
        session.commit()

        return TimeEntryPublic(
            id=te.id,
            worklog_id=te.worklog_id,
            hours=te.hours,
            rate=te.rate,
            description=te.description,
            entry_date=te.entry_date,
            created_at=te.created_at,
            earnings=te.hours * te.rate,
        )

    @staticmethod
    def get_tasks(session: Session, skip: int = 0, limit: int = 100) -> list[TaskPublic]:
        """
        Get all tasks.
        """
        statement = select(Task).offset(skip).limit(limit)
        tasks = session.exec(statement).all()
        return [
            TaskPublic(
                id=t.id,
                title=t.title,
                description=t.description,
                created_at=t.created_at,
            )
            for t in tasks
        ]

    @staticmethod
    def get_freelancers(session: Session, skip: int = 0, limit: int = 100) -> list[UserPublic]:
        """
        Get all users (freelancers).
        """
        statement = select(User).offset(skip).limit(limit)
        users = session.exec(statement).all()
        return [
            UserPublic(
                id=u.id,
                email=u.email,
                is_active=u.is_active,
                is_superuser=u.is_superuser,
                full_name=u.full_name,
            )
            for u in users
        ]

