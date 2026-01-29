import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlmodel import Session, select

from app.financials.models import (
    Adjustment,
    AdjustmentStatus,
    Remittance,
    RemittanceState,
    SettlementRun,
    TaskStatus,
    TaskStatusState,
    Transaction,
    TransactionType,
    Wallet,
)
from app.tasks.models import RemittanceStatus, TimeSegment, TimeSegmentStatus, WorkLog, Task
from app.models import User

logger = logging.getLogger(__name__)


class FinancialService:
    @staticmethod
    def get_or_create_wallet(session: Session, user_id: uuid.UUID) -> Wallet:
        wallet = session.exec(select(Wallet).where(Wallet.user_id == user_id)).first()
        if not wallet:
            wallet = Wallet(user_id=user_id)
            session.add(wallet)
            session.flush()
            session.refresh(wallet)
        return wallet

    @staticmethod
    def calculate_worklog_amounts(
        session: Session, worklog_id: uuid.UUID, include_accrued: bool = False
    ) -> dict:
        worklog = session.get(WorkLog, worklog_id)
        if not worklog:
            return {"accrued": Decimal(0), "remitted": Decimal(0)}

        accrued = Decimal(0)
        remitted = Decimal(0)

        for segment in worklog.time_segments:
            # Always use the rate at recording if available, else fallback to current task rate
            rate = segment.rate_at_recording or worklog.task.rate_amount
            amount = segment.duration_hours * rate

            if segment.status == TimeSegmentStatus.SETTLED:
                remitted += amount
            elif include_accrued and segment.status in [
                TimeSegmentStatus.APPROVED,
                TimeSegmentStatus.PENDING,
            ]:
                accrued += amount

        return {"accrued": accrued, "remitted": remitted}

    @staticmethod
    def run_settlement_process(session: Session, task_id: uuid.UUID, admin_user_id: uuid.UUID | None = None):
        """
        Background task logic for settlement.
        Uses commit() as it runs outside the request-response cycle.
        """
        task_status = session.get(TaskStatus, task_id)
        if not task_status:
            return

        task_status.status = TaskStatusState.PROCESSING
        session.add(task_status)
        session.commit()

        try:
            # 1. Create SettlementRun
            settlement_run = SettlementRun(
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc),
                status="PROCESSING",
                task_id=task_id,
            )
            session.add(settlement_run)
            session.commit()
            session.refresh(settlement_run)

            # 2. Get eligible segments (not remitted, not disputed)
            statement = select(TimeSegment).where(
                TimeSegment.remittance_id.is_(None),
                TimeSegment.status != TimeSegmentStatus.DISPUTED,
            )
            
            if admin_user_id:
                statement = statement.join(WorkLog).join(Task).where(Task.created_by_id == admin_user_id)
                
            eligible_segments = session.exec(statement).all()

            # Group by Worker
            segments_by_worker = {}
            for seg in eligible_segments:
                worker_id = seg.work_log.worker_id
                if worker_id not in segments_by_worker:
                    segments_by_worker[worker_id] = []
                segments_by_worker[worker_id].append(seg)

            total_workers = len(segments_by_worker)
            processed_workers = 0

            if admin_user_id:
                admin_user = session.get(User, admin_user_id)
            else:
                admin_user = session.exec(select(User).where(User.is_superuser)).first()

            if not admin_user:
                raise Exception("No admin user found to pay from")
            admin_wallet = FinancialService.get_or_create_wallet(session, admin_user.id)

            for worker_id, segments in segments_by_worker.items():
                total_worker_amount = Decimal(0)
                segments_to_process = []

                for seg in segments:
                    rate = seg.rate_at_recording or seg.work_log.task.rate_amount
                    amount = seg.duration_hours * rate
                    total_worker_amount += amount
                    segments_to_process.append(seg)
                
                logger.info(f"Worker {worker_id} has {len(segments)} segments, total amount: {total_worker_amount}")

                # Deduct pending adjustments (FIFO)
                adj_statement = (
                    select(Adjustment)
                    .join(TimeSegment, Adjustment.time_segment_id == TimeSegment.id)
                    .join(WorkLog)
                    .where(
                        Adjustment.status == AdjustmentStatus.PENDING,
                        WorkLog.worker_id == worker_id,
                    )
                    .order_by(Adjustment.created_at)
                )
                adjustments = session.exec(adj_statement).all()

                applied_adjustments = []
                remaining_earnings = total_worker_amount

                for adj in adjustments:
                    if adj.amount < 0:
                        deduction = abs(adj.amount)
                        # Only link if we can cover it
                        if remaining_earnings >= deduction:
                            remaining_earnings -= deduction
                            adj.status = AdjustmentStatus.PAID
                            applied_adjustments.append(adj)
                        else:
                            # Stop linking further adjustments once we can't cover one
                            break
                    else:
                        # Positive adjustments increase earnings
                        remaining_earnings += adj.amount
                        adj.status = AdjustmentStatus.PAID
                        applied_adjustments.append(adj)

                status = RemittanceState.PENDING
                if remaining_earnings <= 0:
                    status = RemittanceState.OFFSET

                # Check liquidity
                if remaining_earnings > 0 and admin_wallet.balance < remaining_earnings:
                    status = RemittanceState.AWAITING_FUNDING

                remittance = Remittance(
                    worker_id=worker_id,
                    settlement_run_id=settlement_run.id,
                    amount=remaining_earnings,
                    status=status,
                    processed_at=datetime.now(timezone.utc),
                )
                session.add(remittance)
                session.commit()
                session.refresh(remittance)

                # Only move funds if we are actually PENDING
                if status == RemittanceState.PENDING:
                    admin_wallet.debit(remaining_earnings)
                    admin_wallet.credit(remaining_earnings, reserve=True)
                    session.add(admin_wallet)
                    
                    # Log Admin movement
                    txn_admin = Transaction(
                        wallet_id=admin_wallet.id,
                        amount=remaining_earnings,
                        transaction_type=TransactionType.DEBIT,
                        description=f"Locked funds for Remittance {remittance.id} (Run {settlement_run.id})",
                        reference_id=remittance.id
                    )
                    session.add(txn_admin)

                for seg in segments_to_process:
                    seg.remittance_id = remittance.id
                    # Status is SETTLED only if the remittance isn't blocked by funding
                    if status != RemittanceState.AWAITING_FUNDING:
                        seg.status = TimeSegmentStatus.SETTLED
                    session.add(seg)

                    wl = seg.work_log
                    wl.remittance_status = RemittanceStatus.REMITTED
                    # Increment worklog amount by what was actually settled
                    rate = seg.rate_at_recording or wl.task.rate_amount
                    wl.amount += seg.duration_hours * rate
                    session.add(wl)

                for adj in applied_adjustments:
                    adj.remittance_id = remittance.id
                    session.add(adj)

                processed_workers += 1
                task_status.progress_percentage = int(
                    (processed_workers / total_workers) * 100
                )
                session.add(task_status)
                session.commit()

            task_status.status = TaskStatusState.COMPLETED
            task_status.message = (
                f"Successfully processed {processed_workers} remittances."
            )
            session.add(task_status)
            session.commit()

        except Exception as e:
            logger.error(f"Settlement failed: {e}")
            task_status.status = TaskStatusState.FAILED
            task_status.message = str(e)
            session.add(task_status)
            session.commit()

    @staticmethod
    def cancel_remittance(session: Session, remittance_id: uuid.UUID):
        remittance = session.get(Remittance, remittance_id)
        if not remittance or remittance.status != RemittanceState.PENDING:
            raise HTTPException(status_code=400, detail="Cannot pause this remittance")

        remittance.status = RemittanceState.AWAITING_APPROVAL
        session.add(remittance)
        session.flush()
        session.refresh(remittance)
        return remittance

    @staticmethod
    def approve_remittance(session: Session, remittance_id: uuid.UUID, admin_user_id: uuid.UUID | None = None):
        """
        Approves a paused remittance, moving funds from admin reserve to worker balance.
        """
        remittance = session.get(Remittance, remittance_id)
        if not remittance or remittance.status != RemittanceState.AWAITING_APPROVAL:
            raise HTTPException(status_code=400, detail="Only remittances in AWAITING_APPROVAL can be approved")

        from app.models import User
        if admin_user_id:
            admin_user = session.get(User, admin_user_id)
        else:
            admin_user = session.exec(select(User).where(User.is_superuser)).first()
        
        if not admin_user:
            raise Exception("No admin user found")
            
        admin_wallet = FinancialService.get_or_create_wallet(session, admin_user.id)
        worker_wallet = FinancialService.get_or_create_wallet(session, remittance.worker_id)
        
        # Move funds: Reserve -> Worker Balance
        admin_wallet.debit(remittance.amount, reserve=True)
        worker_wallet.credit(remittance.amount)
        
        remittance.status = RemittanceState.COMPLETED
        remittance.processed_at = datetime.now(timezone.utc)
        
        txn = Transaction(
            wallet_id=worker_wallet.id,
            amount=remittance.amount,
            transaction_type=TransactionType.CREDIT,
            description=f"Manual Approval of Remittance {remittance.id}",
            reference_id=remittance.id
        )
        
        session.add(admin_wallet)
        session.add(worker_wallet)
        session.add(remittance)
        session.add(txn)
        session.flush()
        session.refresh(remittance)
        return remittance

    @staticmethod
    def reject_remittance(session: Session, remittance_id: uuid.UUID, admin_user_id: uuid.UUID | None = None):
        """
        Rejects a remittance, returning funds from reserve to balance.
        """
        remittance = session.get(Remittance, remittance_id)
        if not remittance or remittance.status not in [RemittanceState.PENDING, RemittanceState.AWAITING_APPROVAL]:
            raise HTTPException(status_code=400, detail="Remittance cannot be rejected")

        from app.models import User
        if admin_user_id:
            admin_user = session.get(User, admin_user_id)
        else:
            admin_user = session.exec(select(User).where(User.is_superuser)).first()
        
        admin_wallet = FinancialService.get_or_create_wallet(session, admin_user.id)
        
        # Revert funds
        admin_wallet.debit(remittance.amount, reserve=True)
        admin_wallet.credit(remittance.amount)
        
        remittance.status = RemittanceState.CANCELLED
        
        txn = Transaction(
            wallet_id=admin_wallet.id,
            amount=remittance.amount,
            transaction_type=TransactionType.CREDIT,
            description=f"Reverted funds from rejected Remittance {remittance.id}",
            reference_id=remittance.id
        )
        
        session.add(admin_wallet)
        session.add(remittance)
        session.add(txn)
        session.flush()
        session.refresh(remittance)
        return remittance

    @staticmethod
    def finalize_pending_payouts(session: Session, admin_user_id: uuid.UUID | None = None):
        """
        Reconciliation Phase A: Auto-complete payouts past the delay window.
        Uses commit() as it runs in a scheduler job.
        """
        from app.core.config import settings

        delay_window = timedelta(hours=settings.REMITTANCE_DELAY_HOURS)
        cutoff_time = datetime.now(timezone.utc) - delay_window

        statement = select(Remittance).where(
            Remittance.status == RemittanceState.PENDING,
            Remittance.created_at <= cutoff_time,
        )
        pending_remittances = session.exec(statement).all()

        if admin_user_id:
            admin_user = session.get(User, admin_user_id)
        else:
            admin_user = session.exec(select(User).where(User.is_superuser)).first()

        if not admin_user:
            logger.error("No admin user found for reconciliation")
            return
        admin_wallet = FinancialService.get_or_create_wallet(session, admin_user.id)

        for remittance in pending_remittances:
            try:
                worker_wallet = FinancialService.get_or_create_wallet(
                    session, remittance.worker_id
                )

                admin_wallet.debit(remittance.amount, reserve=True)
                worker_wallet.credit(remittance.amount)

                remittance.status = RemittanceState.COMPLETED
                remittance.processed_at = datetime.now(timezone.utc)

                txn = Transaction(
                    wallet_id=worker_wallet.id,
                    amount=remittance.amount,
                    transaction_type=TransactionType.CREDIT,
                    description=f"Auto-finalized Remittance {remittance.id}",
                    reference_id=remittance.id,
                )

                session.add(admin_wallet)
                session.add(worker_wallet)
                session.add(remittance)
                session.add(txn)
                session.commit()
                logger.info(
                    f"Auto-finalized remittance {remittance.id} for worker {remittance.worker_id}"
                )
            except Exception as e:
                logger.error(f"Failed to finalize remittance {remittance.id}: {e}")
                session.rollback()

    @staticmethod
    def retry_awaiting_funding(session: Session, admin_user_id: uuid.UUID | None = None):
        """
        Identify settlements that failed due to admin balance and retry if funds are now available.
        Uses commit() as it runs in a scheduler job.
        """
        if admin_user_id:
            admin_user = session.get(User, admin_user_id)
        else:
            admin_user = session.exec(select(User).where(User.is_superuser)).first()

        if not admin_user:
            return
        admin_wallet = FinancialService.get_or_create_wallet(session, admin_user.id)

        statement = select(Remittance).where(
            Remittance.status == RemittanceState.AWAITING_FUNDING
        )
        blocked_remittances = session.exec(statement).all()

        for remittance in blocked_remittances:
            if admin_wallet.balance >= remittance.amount:
                try:
                    admin_wallet.debit(remittance.amount)
                    admin_wallet.credit(remittance.amount, reserve=True)
                    remittance.status = RemittanceState.PENDING

                    session.add(admin_wallet)
                    session.add(remittance)
                    session.commit()
                    logger.info(
                        f"Successfully funded previously blocked remittance {remittance.id}"
                    )
                except Exception as e:
                    logger.error(f"Failed to fund remittance {remittance.id}: {e}")
                    session.rollback()