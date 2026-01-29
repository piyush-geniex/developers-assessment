from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.config import settings
from app.tasks.models import TimeSegmentStatus, RemittanceStatus
from app.tasks.service import TaskService
from app.tasks.schemas import TaskCreate, WorkLogCreate, TimeSegmentCreate
from app.models import User

def test_create_task(client: TestClient, superuser_token_headers: dict[str, str]):
    response = client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=superuser_token_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "rate_amount": "15.50",
            "currency": "USD",
        },
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == "Test Task"
    assert float(content["rate_amount"]) == 15.50


def test_create_task_admin_only(client: TestClient, normal_user_token_headers: dict[str, str]):
    response = client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=normal_user_token_headers,
        json={
            "title": "Unauthorized Task",
            "rate_amount": "10.00"
        },
    )
    assert response.status_code == 403

def test_list_all_worklogs_comprehensive(client: TestClient, superuser_token_headers: dict[str, str], db: Session):
    from sqlmodel import select
    # Setup: Create a task and worklog with various segments
    admin = db.exec(select(User).where(User.is_superuser)).first()
    task = TaskService.create_task(db, TaskCreate(title="Comp Test Task", rate_amount=Decimal("100.00")), admin.id)
    wl = TaskService.create_worklog(db, WorkLogCreate(task_id=task.id, worker_id=admin.id))
    
    # 1. Settled segment ($100 * 1 = $100)
    seg1 = TaskService.create_timesegment(db, TimeSegmentCreate(
        work_log_id=wl.id, start_time="2024-01-01T09:00:00Z", end_time="2024-01-01T10:00:00Z", duration_hours=Decimal("1.0")
    ))
    TaskService.update_timesegment(db, seg1.id, {"status": TimeSegmentStatus.SETTLED})
    
    # 2. Approved segment ($100 * 2 = $200) - Should be in accrued
    seg2 = TaskService.create_timesegment(db, TimeSegmentCreate(
        work_log_id=wl.id, start_time="2024-01-01T11:00:00Z", end_time="2024-01-01T13:00:00Z", duration_hours=Decimal("2.0")
    ))
    TaskService.update_timesegment(db, seg2.id, {"status": TimeSegmentStatus.APPROVED})
    
    # 3. Pending segment ($100 * 0.5 = $50) - Should be in accrued
    TaskService.create_timesegment(db, TimeSegmentCreate(
        work_log_id=wl.id, start_time="2024-01-01T14:00:00Z", end_time="2024-01-01T14:30:00Z", duration_hours=Decimal("0.5")
    ))
    
    # 4. Disputed segment ($100 * 5 = $500) - Should be IGNORED
    seg4 = TaskService.create_timesegment(db, TimeSegmentCreate(
        work_log_id=wl.id, start_time="2024-01-01T15:00:00Z", end_time="2024-01-01T20:00:00Z", duration_hours=Decimal("5.0")
    ))
    TaskService.dispute_timesegment(db, seg4.id, "Dispute")
    
    db.commit()

    # Test A: includeAccrued=false (default)
    response = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    my_wl = next(item for item in content if item["id"] == str(wl.id))
    assert Decimal(str(my_wl["amount"])) == Decimal("100.00")
    assert "accrued_amount" not in my_wl

    # Test B: includeAccrued=true
    response = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs?includeAccrued=true",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    my_wl = next(item for item in content if item["id"] == str(wl.id))
    assert Decimal(str(my_wl["amount"])) == Decimal("100.00")
    # Accrued = Approved(200) + Pending(50) = 250
    assert Decimal(str(my_wl["accrued_amount"])) == Decimal("250.00")

