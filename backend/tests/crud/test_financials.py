import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlmodel import Session, select
from app.financials.service import FinancialService
from app.financials.models import Remittance, RemittanceState, Adjustment, AdjustmentStatus, Wallet, TaskStatus
from app.tasks.models import Task, WorkLog, TimeSegment, TimeSegmentStatus
from app.tasks.service import TaskService
from app.tasks.schemas import TaskCreate, WorkLogCreate, TimeSegmentCreate
from app.models import User

def test_reserve_fund_lock(db: Session):
    # Create unique admin and worker
    admin = User(email=f"admin-{uuid.uuid4()}@example.com", hashed_password="pw", is_superuser=True)
    worker = User(email=f"worker-{uuid.uuid4()}@example.com", hashed_password="pw")
    db.add(admin)
    db.add(worker)
    db.flush()

    # Setup Admin Wallet
    admin_wallet = FinancialService.get_or_create_wallet(db, admin.id)
    admin_wallet.balance = Decimal("1000.00")
    admin_wallet.reserve = Decimal("0.00")
    db.add(admin_wallet)
    db.flush()

    # Setup Work
    task = TaskService.create_task(db, TaskCreate(title="Reserve Test", rate_amount=Decimal("100.00")), admin.id)
    wl = TaskService.create_worklog(db, WorkLogCreate(task_id=task.id, worker_id=worker.id))
    seg = TaskService.create_timesegment(db, TimeSegmentCreate(
        work_log_id=wl.id, start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc), duration_hours=Decimal("2.0")
    ))
    # Approve it
    TaskService.update_timesegment(db, seg.id, {"status": TimeSegmentStatus.APPROVED})
    db.flush() # Amount should be $200

    # Start Settlement
    task_status = TaskStatus(task_type="TEST")
    db.add(task_status)
    db.flush()
    
    FinancialService.run_settlement_process(db, task_status.id, admin.id)
    
    # Re-fetch wallet
    admin_wallet = db.exec(select(Wallet).where(Wallet.user_id == admin.id)).first()
    assert admin_wallet.balance == Decimal("800.00")
    assert admin_wallet.reserve == Decimal("200.00")

def test_offset_debt_recovery(db: Session):
    admin = User(email=f"admin-{uuid.uuid4()}@example.com", hashed_password="pw", is_superuser=True)
    worker = User(email=f"worker-{uuid.uuid4()}@example.com", hashed_password="pw")
    db.add(admin)
    db.add(worker)
    db.flush()

    admin_wallet = FinancialService.get_or_create_wallet(db, admin.id)
    admin_wallet.balance = Decimal("1000.00")
    db.add(admin_wallet)
    db.flush()

    # Setup Work ($100 earnings)
    task = Task(title="Offset Test", rate_amount=Decimal("100.00"), created_by_id=admin.id)
    db.add(task)
    db.flush()
    wl = WorkLog(task_id=task.id, worker_id=worker.id)
    db.add(wl)
    db.flush()
    seg = TimeSegment(work_log_id=wl.id, duration_hours=Decimal("1.0"), rate_at_recording=Decimal("100.00"), start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc))
    db.add(seg)
    db.flush()
    
    # Setup two negative Adjustments that sum to -$100 (exactly offsetting earnings)
    adj1 = Adjustment(time_segment_id=seg.id, amount=Decimal("-50.00"), reason="Debt 1", status=AdjustmentStatus.PENDING, effective_date=datetime.now(timezone.utc))
    adj2 = Adjustment(time_segment_id=seg.id, amount=Decimal("-50.00"), reason="Debt 2", status=AdjustmentStatus.PENDING, effective_date=datetime.now(timezone.utc))
    db.add(adj1)
    db.add(adj2)
    db.flush()
    
    # Run Settlement
    task_status = TaskStatus(task_type="TEST_OFFSET")
    db.add(task_status)
    db.flush()
    
    FinancialService.run_settlement_process(db, task_status.id, admin.id)
    
    # Verify OFFSET
    remittance = db.exec(select(Remittance).where(Remittance.worker_id == worker.id)).first()
    assert remittance.status == RemittanceState.OFFSET
    assert remittance.amount == Decimal("0.00")
    
    db.refresh(adj1)
    db.refresh(adj2)
    assert adj1.status == AdjustmentStatus.PAID
    assert adj2.status == AdjustmentStatus.PAID

def test_awaiting_funding_and_retry(db: Session):
    admin = User(email=f"admin-{uuid.uuid4()}@example.com", hashed_password="pw", is_superuser=True)
    worker = User(email=f"worker-{uuid.uuid4()}@example.com", hashed_password="pw")
    db.add(admin)
    db.add(worker)
    db.flush()

    admin_wallet = FinancialService.get_or_create_wallet(db, admin.id)
    admin_wallet.balance = Decimal("0.00")
    db.add(admin_wallet)
    db.flush()

    task = TaskService.create_task(db, TaskCreate(title="Funding Test", rate_amount=Decimal("100.00")), admin.id)
    wl = TaskService.create_worklog(db, WorkLogCreate(task_id=task.id, worker_id=worker.id))
    TaskService.create_timesegment(db, TimeSegmentCreate(
        work_log_id=wl.id, start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc), duration_hours=Decimal("1.0")
    ))
    db.flush()

    task_status = TaskStatus(task_type="TEST_FUNDING")
    db.add(task_status)
    db.flush()
    FinancialService.run_settlement_process(db, task_status.id, admin.id)

    remittance = db.exec(select(Remittance).where(Remittance.worker_id == worker.id)).first()
    assert remittance.status == RemittanceState.AWAITING_FUNDING

    admin_wallet.balance = Decimal("500.00")
    db.add(admin_wallet)
    db.flush()

    FinancialService.retry_awaiting_funding(db, admin.id)
    
    db.refresh(remittance)
    assert remittance.status == RemittanceState.PENDING
    
    db.refresh(admin_wallet)
    assert admin_wallet.balance == Decimal("400.00")
    assert admin_wallet.reserve == Decimal("100.00")

def test_aggregation_of_multiple_worklogs(db: Session):
    admin = User(email=f"admin-{uuid.uuid4()}@example.com", hashed_password="pw", is_superuser=True)
    worker = User(email=f"worker-{uuid.uuid4()}@example.com", hashed_password="pw")
    db.add(admin)
    db.add(worker)
    db.flush()
    
    admin_wallet = FinancialService.get_or_create_wallet(db, admin.id)
    admin_wallet.balance = Decimal("1000.00")
    db.add(admin_wallet)
    db.flush()

    t1 = TaskService.create_task(db, TaskCreate(title="Task 1", rate_amount=Decimal("10.00")), admin.id)
    t2 = TaskService.create_task(db, TaskCreate(title="Task 2", rate_amount=Decimal("20.00")), admin.id)
    
    wl1 = TaskService.create_worklog(db, WorkLogCreate(task_id=t1.id, worker_id=worker.id))
    wl2 = TaskService.create_worklog(db, WorkLogCreate(task_id=t2.id, worker_id=worker.id))
    
    TaskService.create_timesegment(db, TimeSegmentCreate(work_log_id=wl1.id, duration_hours=Decimal("5"), start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc)))
    TaskService.create_timesegment(db, TimeSegmentCreate(work_log_id=wl2.id, duration_hours=Decimal("5"), start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc)))
    db.flush()

    task_status = TaskStatus(task_type="TEST_AGGREGATION")
    db.add(task_status)
    db.flush()
    FinancialService.run_settlement_process(db, task_status.id, admin.id)

    remittances = db.exec(select(Remittance).where(Remittance.worker_id == worker.id)).all()
    assert len(remittances) == 1
    assert remittances[0].amount == Decimal("150.00")

def test_phase_a_reconciliation(db: Session):
    admin = User(email=f"admin-{uuid.uuid4()}@example.com", hashed_password="pw", is_superuser=True)
    worker = User(email=f"worker-{uuid.uuid4()}@example.com", hashed_password="pw")
    db.add(admin)
    db.add(worker)
    db.flush()
    
    admin_wallet = FinancialService.get_or_create_wallet(db, admin.id)
    admin_wallet.balance = Decimal("1000.00")
    admin_wallet.reserve = Decimal("100.00")
    db.add(admin_wallet)
    
    worker_wallet = FinancialService.get_or_create_wallet(db, worker.id)
    worker_wallet.balance = Decimal("0.00")
    db.add(worker_wallet)
    db.flush()

    old_date = datetime.now(timezone.utc) - timedelta(hours=48)
    remittance = Remittance(
        worker_id=worker.id,
        amount=Decimal("100.00"),
        status=RemittanceState.PENDING,
        created_at=old_date
    )
    db.add(remittance)
    db.flush()

    FinancialService.finalize_pending_payouts(db, admin.id)
    
    db.refresh(remittance)
    assert remittance.status == RemittanceState.COMPLETED
    db.refresh(worker_wallet)
    assert worker_wallet.balance == Decimal("100.00")
    db.refresh(admin_wallet)
    assert admin_wallet.reserve == Decimal("0.00")

def test_partial_adjustment_coverage(db: Session):
    admin = User(email=f"admin-{uuid.uuid4()}@example.com", hashed_password="pw", is_superuser=True)
    worker = User(email=f"worker-{uuid.uuid4()}@example.com", hashed_password="pw")
    db.add(admin)
    db.add(worker)
    db.flush()
    
    admin_wallet = FinancialService.get_or_create_wallet(db, admin.id)
    admin_wallet.balance = Decimal("1000.00")
    db.add(admin_wallet)
    db.flush()

    task = Task(title="Partial Test", rate_amount=Decimal("100.00"), created_by_id=admin.id)
    db.add(task)
    db.flush()
    wl = WorkLog(task_id=task.id, worker_id=worker.id)
    db.add(wl)
    db.flush()
    seg = TimeSegment(work_log_id=wl.id, duration_hours=Decimal("1.0"), rate_at_recording=Decimal("100.00"), start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc))
    db.add(seg)
    db.flush()

    adj1 = Adjustment(time_segment_id=seg.id, amount=Decimal("-60.00"), reason="Adj 1", status=AdjustmentStatus.PENDING, effective_date=datetime.now(timezone.utc))
    adj2 = Adjustment(time_segment_id=seg.id, amount=Decimal("-70.00"), reason="Adj 2", status=AdjustmentStatus.PENDING, effective_date=datetime.now(timezone.utc))
    db.add(adj1)
    db.add(adj2)
    db.flush()

    task_status = TaskStatus(task_type="TEST_PARTIAL")
    db.add(task_status)
    db.flush()
    FinancialService.run_settlement_process(db, task_status.id, admin.id)

    remittance = db.exec(select(Remittance).where(Remittance.worker_id == worker.id)).first()
    assert remittance.amount == Decimal("40.00")
    
    db.refresh(adj1)
    db.refresh(adj2)
    assert adj1.status == AdjustmentStatus.PAID
    assert adj2.status == AdjustmentStatus.PENDING

def test_exact_offset_status(db: Session):
    admin = User(email=f"admin-{uuid.uuid4()}@example.com", hashed_password="pw", is_superuser=True)
    worker = User(email=f"worker-{uuid.uuid4()}@example.com", hashed_password="pw")
    db.add(admin)
    db.add(worker)
    db.flush()
    
    admin_wallet = FinancialService.get_or_create_wallet(db, admin.id)
    admin_wallet.balance = Decimal("1000.00")
    db.add(admin_wallet)
    db.flush()

    task = Task(title="Exact Test", rate_amount=Decimal("100.00"), created_by_id=admin.id)
    db.add(task)
    db.flush()
    wl = WorkLog(task_id=task.id, worker_id=worker.id)
    db.add(wl)
    db.flush()
    seg = TimeSegment(work_log_id=wl.id, duration_hours=Decimal("1.0"), rate_at_recording=Decimal("100.00"), start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc))
    db.add(seg)
    db.flush()
    adj = Adjustment(time_segment_id=seg.id, amount=Decimal("-100.00"), reason="Exact", status=AdjustmentStatus.PENDING, effective_date=datetime.now(timezone.utc))
    db.add(adj)
    db.flush()

    task_status = TaskStatus(task_type="TEST_EXACT")
    db.add(task_status)
    db.flush()
    FinancialService.run_settlement_process(db, task_status.id, admin.id)

    remittance = db.exec(select(Remittance).where(Remittance.worker_id == worker.id)).first()
    assert remittance.status == RemittanceState.OFFSET
    assert remittance.amount == Decimal("0.00")
    
    db.refresh(admin_wallet)
    assert admin_wallet.reserve == Decimal("0.00")

def test_reconciliation_skips_awaiting_approval(db: Session):
    admin = User(email=f"admin-{uuid.uuid4()}@example.com", hashed_password="pw", is_superuser=True)
    worker = User(email=f"worker-{uuid.uuid4()}@example.com", hashed_password="pw")
    db.add(admin)
    db.add(worker)
    db.flush()
    
    old_date = datetime.now(timezone.utc) - timedelta(hours=48)
    remittance = Remittance(
        worker_id=worker.id,
        amount=Decimal("100.00"),
        status=RemittanceState.AWAITING_APPROVAL,
        created_at=old_date
    )
    db.add(remittance)
    db.flush()

    FinancialService.finalize_pending_payouts(db, admin.id)
    
    db.refresh(remittance)
    assert remittance.status == RemittanceState.AWAITING_APPROVAL
