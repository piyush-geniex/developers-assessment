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
    WorkLogListItem,
    PaymentBatchPreview,
    ConfirmPaymentRequest,
    RemittancePublic,
)
from app.api.routes.worklogs.service import WorkLogService


class PaymentService:
    @staticmethod
    def get_payment_preview(
        session: Session,
        current_user: Any,
        date_from: str,
        date_to: str,
    ) -> PaymentBatchPreview:
        """Get worklogs eligible for payment in the given date range (unremitted only)."""
        date_conds = [TimeEntry.work_log_id == WorkLog.id]
        date_conds.append(TimeEntry.entry_date >= date_from)
        date_conds.append(TimeEntry.entry_date <= date_to)
        date_filter = select(1).where(and_(*date_conds)).exists()

        statement = (
            select(WorkLog)
            .join(Task, WorkLog.task_id == Task.id)
            .join(User, WorkLog.user_id == User.id)
            .where(WorkLog.remittance_id.is_(None))
            .where(date_filter)
        )
        work_logs = session.exec(statement).all()

        items: list[WorkLogListItem] = []
        total_cents = 0
        for wl in work_logs:
            wl = session.get(WorkLog, wl.id)
            if not wl or not wl.task or not wl.user:
                continue
            amount = WorkLogService._work_log_amount_cents(session, wl.id)
            total_cents += amount
            items.append(
                WorkLogListItem(
                    id=wl.id,
                    task_id=wl.task_id,
                    task_title=wl.task.title,
                    user_id=wl.user_id,
                    user_email=wl.user.email,
                    user_full_name=wl.user.full_name,
                    amount_cents=amount,
                    remittance_id=None,
                    remittance_status=None,
                )
            )

        return PaymentBatchPreview(
            work_logs=items,
            total_amount_cents=total_cents,
            period_start=date_from,
            period_end=date_to,
        )

    @staticmethod
    def confirm_payment(
        session: Session,
        current_user: Any,
        body: ConfirmPaymentRequest,
    ) -> list[RemittancePublic]:
        """
        Create remittances for the selected worklogs.         Excludes worklogs not in
        include_work_log_ids and skips freelancers in exclude_freelancer_ids.
        """
        exclude_ids = set(body.exclude_freelancer_ids or [])
        include_work_log_ids = set(body.include_work_log_ids)

        # Load worklogs that are included and not from excluded freelancers
        stmt = (
            select(WorkLog)
            .join(User, WorkLog.user_id == User.id)
            .where(WorkLog.id.in_(include_work_log_ids))
            .where(WorkLog.remittance_id.is_(None))
        )
        if exclude_ids:
            stmt = stmt.where(WorkLog.user_id.notin_(exclude_ids))
        work_logs = session.exec(stmt).all()

        # Group by user_id to create one remittance per freelancer
        by_user: dict[uuid.UUID, list[WorkLog]] = {}
        for wl in work_logs:
            wl = session.get(WorkLog, wl.id)
            if not wl or wl.user_id in exclude_ids:
                continue
            by_user.setdefault(wl.user_id, []).append(wl)

        remittances_created: list[Remittance] = []
        for user_id, user_work_logs in by_user.items():
            total_cents = sum(
                WorkLogService._work_log_amount_cents(session, wl.id)
                for wl in user_work_logs
            )
            remittance = Remittance(
                user_id=user_id,
                period_start=body.period_start,
                period_end=body.period_end,
                status=RemittanceStatus.PENDING,
                total_amount_cents=total_cents,
            )
            session.add(remittance)
            session.flush()  # get remittance.id
            for wl in user_work_logs:
                wl.remittance_id = remittance.id
                session.add(wl)
            remittances_created.append(remittance)

        session.commit()
        for remittance in remittances_created:
            session.refresh(remittance)
        return [
            RemittancePublic(
                id=r.id,
                user_id=r.user_id,
                period_start=r.period_start,
                period_end=r.period_end,
                status=r.status,
                total_amount_cents=r.total_amount_cents,
            )
            for r in remittances_created
        ]