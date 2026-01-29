import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlmodel import Session, select, create_engine

from app.core.config import settings
from app.models import User
from app.tasks.models import Task, WorkLog, TimeSegment, Dispute, TimeSegmentStatus, RemittanceStatus
from app.financials.models import Wallet, Transaction, TransactionType, Remittance, RemittanceState, Adjustment, AdjustmentStatus, SettlementRun, TaskStatus, TaskStatusState
from app.tasks.service import TaskService
from app.financials.service import FinancialService
from app.tasks.schemas import TaskCreate, WorkLogCreate, TimeSegmentCreate, DisputeCreate, TaskUpdate, WorkLogPublic, TimeSegmentUpdate


def populate_sample_data():
    # Connect to the database
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    with Session(engine) as session:
        # Find the superuser using the actual email that exists in the database
        admin_user = session.exec(
            select(User).where(User.email == "superuser@example.com")
        ).first()

        if not admin_user:
            print("Superuser not found!")
            return
        
        print(f"Found admin user: {admin_user.email}")
        
        # Create a worker user if not exists
        existing_worker = session.exec(
            select(User).where(User.email == "worker@example.com")
        ).first()

        if existing_worker:
            worker_user = existing_worker
            print(f"Using existing worker user: {worker_user.email}")
        else:
            worker_user = User(
                email="worker@example.com",
                hashed_password="hashed_worker_password",  # This would normally be hashed
                is_active=True,
                is_superuser=False,
                full_name="Test Worker"
            )
            session.add(worker_user)
            session.commit()
            session.refresh(worker_user)

            print(f"Created worker user: {worker_user.email}")
        
        # Create a task
        task_create = TaskCreate(
            title="Development Task",
            rate_amount=Decimal("50.00"),
            description="Software development work"
        )
        task = TaskService.create_task(session, task_create, admin_user.id)
        print(f"Created task: {task.title}")

        # Create a worklog
        worklog_create = WorkLogCreate(task_id=task.id, worker_id=worker_user.id)
        worklog = TaskService.create_worklog(session, worklog_create)
        print(f"Created worklog for worker {worker_user.email}")

        # Create time segments
        time_segment_1 = TaskService.create_timesegment(
            session,
            TimeSegmentCreate(
                work_log_id=worklog.id,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc).replace(hour=10),
                duration_hours=Decimal("4.0"),
                status=TimeSegmentStatus.APPROVED
            )
        )
        print(f"Created time segment 1: {time_segment_1.duration_hours} hours")

        time_segment_2 = TaskService.create_timesegment(
            session,
            TimeSegmentCreate(
                work_log_id=worklog.id,
                start_time=datetime.now(timezone.utc).replace(hour=11),
                end_time=datetime.now(timezone.utc).replace(hour=15),
                duration_hours=Decimal("4.0"),
                status=TimeSegmentStatus.SETTLED
            )
        )
        print(f"Created time segment 2: {time_segment_2.duration_hours} hours")

        # Create a dispute for one of the segments
        dispute = TaskService.dispute_timesegment(
            session,
            time_segment_1.id,
            "Quality issue with work"
        )
        print(f"Created dispute for time segment")

        # Resolve the dispute
        resolved_dispute = TaskService.resolve_dispute(
            session,
            dispute.id,
            "Issue resolved with additional work",
            True  # approved
        )
        print(f"Resolved dispute")
        
        # Create wallets for both users
        admin_wallet = FinancialService.get_or_create_wallet(session, admin_user.id)
        admin_wallet.balance = Decimal("10000.00")  # Give admin plenty of funds
        session.add(admin_wallet)
        
        worker_wallet = FinancialService.get_or_create_wallet(session, worker_user.id)
        worker_wallet.balance = Decimal("100.00")
        session.add(worker_wallet)
        
        session.commit()
        print(f"Created wallets for admin and worker")
        
        # Run settlement process to generate remittances
        task_status = TaskStatus(task_type="SETTLEMENT_RUN")
        session.add(task_status)
        session.commit()
        session.refresh(task_status)
        
        print(f"Starting settlement process with task ID: {task_status.id}")
        
        # Run the settlement process
        FinancialService.run_settlement_process(session, task_status.id, admin_user.id)
        
        print("Settlement process completed")
        
        # Commit all changes
        session.commit()
        
        print("Sample data successfully populated!")


if __name__ == "__main__":
    populate_sample_data()