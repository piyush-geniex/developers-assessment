from datetime import date
from typing import List
from app.models import Remittance, RemittanceWorkLog, Task, User, WorkLog
from app.schemas import TaskCreateIn, TaskCreateOut, WorkLogCreateIn
from fastapi import HTTPException
from sqlalchemy import select
from sqlmodel import Session

from typing import List, Optional
from app.models import Remittance, RemittanceWorkLog, Task, User, WorkLog
from app.schemas import TaskCreateIn, TaskCreateOut, WorkLogCreateIn
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlmodel import Session


class WorklogService:
    @staticmethod
    def calculate_worklog_amount(wl: WorkLog) -> float:
        """
        Calculate total amount for a worklog including time segments and adjustments.
        Adjustments can be negative (deductions) or positive (bonuses).
        """
        time_amount = sum(ts.duration for ts in wl.time_segments)
        adjustments_amount = sum(adj.amount for adj in wl.adjustments)
        return time_amount + adjustments_amount

    @staticmethod
    def get_remitted_amount(wl: WorkLog) -> float:
        """
        Get total amount already remitted for this worklog.
        Only counts PENDING and PAID remittances (excludes CANCELLED/FAILED).
        """
        total_remitted = 0.0

        # Get all remittances for this worklog's user
        for remittance in wl.user.remittances:
            # Only count successful or pending remittances
            if remittance.status in ("PENDING", "PAID"):
                # Find the specific RemittanceWorkLog entry for this worklog
                for rwl in remittance.remittance_worklogs:
                    if rwl.worklog_id == wl.id:
                        total_remitted += rwl.amount

        return total_remitted

    @staticmethod
    def get_remaining_amount(wl: WorkLog) -> float:
        """
        Calculate how much of this worklog still needs to be remitted.
        Can be negative if there were deductions after payment.
        """
        total_amount = WorklogService.calculate_worklog_amount(wl)
        remitted_amount = WorklogService.get_remitted_amount(wl)
        return total_amount - remitted_amount

    @staticmethod
    def list_worklogs(session: Session, remittance_status: str):
        """
        List all worklogs with financial information.

        Args:
            session: Database session
            remittance_status: Filter by "REMITTED", "UNREMITTED", or "ALL"

        Returns:
            List of worklog dictionaries with amount details
        """
        worklogs = session.exec(select(WorkLog)).scalars().all()
        results = []

        for wl in worklogs:
            total_amount = WorklogService.calculate_worklog_amount(wl)
            remitted_amount = WorklogService.get_remitted_amount(wl)
            remaining_amount = total_amount - remitted_amount

            # A worklog is considered "fully remitted" if remaining <= 0
            # (it's <= 0 because adjustments could make it negative)
            is_fully_remitted = remaining_amount <= 0

            # Apply filter
            if remittance_status == "REMITTED" and not is_fully_remitted:
                continue
            if remittance_status == "UNREMITTED" and is_fully_remitted:
                continue

            results.append({
                "worklog_id": wl.id,
                "user_id": wl.user_id,
                "user_name": wl.user.full_name if wl.user else None,
                "task_id": wl.task_id,
                "task_title": wl.task.title if wl.task else None,
                "total_amount": round(total_amount, 2),
                "remitted_amount": round(remitted_amount, 2),
                "remaining_amount": round(remaining_amount, 2),
                "is_fully_remitted": is_fully_remitted,
                "time_segments_count": len(wl.time_segments),
                "adjustments_count": len(wl.adjustments),
            })

        return results

    @staticmethod
    def generate_remittances(
        session: Session,
        period_start: date,
        period_end: date
    ) -> dict:
        """
        Generate remittances for all users based on unremitted work.

        Key behaviors:
        1. Only includes worklogs with remaining amounts > 0
        2. Handles partial remittances (work already partially paid)
        3. Skips users with no eligible work
        4. Creates RemittanceWorkLog entries tracking exact amounts

        Returns:
            Summary of remittances created
        """
        users = session.exec(select(User)).scalars().all()
        remittances_created = 0
        total_amount_processed = 0.0

        for user in users:
            # Get all worklogs for this user
            user_worklogs = session.exec(
                select(WorkLog).where(WorkLog.user_id == user.id)
            ).scalars().all()

            total_user_amount = 0.0
            worklogs_to_include = []

            for wl in user_worklogs:
                # Calculate remaining amount for this worklog
                remaining = WorklogService.get_remaining_amount(wl)

                # Only include if there's something left to remit
                if remaining > 0:
                    total_user_amount += remaining
                    worklogs_to_include.append((wl, remaining))

            # Skip if nothing to remit for this user
            if total_user_amount <= 0:
                continue

            # Create remittance
            remittance = Remittance(
                user_id=user.id,
                total_amount=total_user_amount,
                status="PENDING",
                period_start=period_start,
                period_end=period_end,
            )
            session.add(remittance)
            session.commit()
            session.refresh(remittance)

            # Create RemittanceWorkLog entries for each worklog
            for wl, amount in worklogs_to_include:
                rwl = RemittanceWorkLog(
                    remittance_id=remittance.id,
                    worklog_id=wl.id,
                    amount=amount,  # Record the exact amount being remitted
                )
                session.add(rwl)

            session.commit()

            remittances_created += 1
            total_amount_processed += total_user_amount

        return {
            "remittances_created": remittances_created,
            "total_amount": round(total_amount_processed, 2),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }

    @staticmethod
    def get_all_remittances(session: Session) -> List[dict]:
        """
        Get all remittances with detailed information.

        Returns:
            List of remittance dictionaries with worklog details
        """
        remittances = session.exec(select(Remittance)).scalars().all()
        results = []

        for rem in remittances:
            worklog_details = []

            for rwl in rem.remittance_worklogs:
                worklog_details.append({
                    "worklog_id": rwl.worklog_id,
                    "amount_remitted": round(rwl.amount, 2),
                    "task_id": rwl.worklog.task_id if rwl.worklog else None,
                })

            results.append({
                "remittance_id": rem.id,
                "user_id": rem.user_id,
                "user_name": rem.user.full_name if rem.user else None,
                "total_amount": round(rem.total_amount, 2),
                "status": rem.status,
                "period_start": rem.period_start.isoformat(),
                "period_end": rem.period_end.isoformat(),
                "created_at": rem.created_at.isoformat() if rem.created_at else None,
                "worklogs": worklog_details,
                "worklog_count": len(worklog_details),
            })

        return results

    @staticmethod
    def create_task(session: Session, task_in: TaskCreateIn) -> TaskCreateOut:
        """Create a new task."""
        task = Task(
            title=task_in.title,
            description=task_in.description,
        )

        session.add(task)
        session.commit()
        session.refresh(task)

        return task

    @staticmethod
    def create_worklog(
        session: Session,
        worklog_in: WorkLogCreateIn,
    ) -> WorkLog:
        """Create a new worklog with validation."""
        # Validate user exists
        user = session.get(User, worklog_in.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate task exists
        task = session.get(Task, worklog_in.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        worklog = WorkLog(
            user_id=worklog_in.user_id,
            task_id=worklog_in.task_id,
        )

        session.add(worklog)
        session.commit()
        session.refresh(worklog)

        return worklog

    @staticmethod
    def update_remittance_status(
        session: Session,
        remittance_id: int,
        new_status: str
    ) -> Remittance:
        """
        Update remittance status (e.g., PENDING → PAID or CANCELLED).
        This is important for handling failed payments.
        """
        remittance = session.get(Remittance, remittance_id)
        if not remittance:
            raise HTTPException(status_code=404, detail="Remittance not found")

        valid_statuses = ["PENDING", "PAID", "CANCELLED", "FAILED"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )

        remittance.status = new_status
        session.add(remittance)
        session.commit()
        session.refresh(remittance)

        return remittance
