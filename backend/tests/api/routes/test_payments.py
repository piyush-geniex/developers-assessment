"""Tests for payment API endpoints."""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import Freelancer, TimeEntry, WorkLog, WorkLogStatus


def create_test_freelancer(session: Session, name: str = "Test Freelancer", hourly_rate: Decimal = Decimal("50.00")) -> Freelancer:
    """Create a test freelancer."""
    freelancer = Freelancer(
        name=name,
        email=f"{name.lower().replace(' ', '.')}_{uuid.uuid4().hex[:6]}@test.com",
        hourly_rate=hourly_rate,
    )
    session.add(freelancer)
    session.commit()
    session.refresh(freelancer)
    return freelancer


def create_test_worklog(
    session: Session,
    freelancer: Freelancer,
    task: str = "Test Task",
    status: WorkLogStatus = WorkLogStatus.PENDING,
) -> WorkLog:
    """Create a test worklog."""
    worklog = WorkLog(
        freelancer_id=freelancer.id,
        task_description=task,
        status=status,
    )
    session.add(worklog)
    session.commit()
    session.refresh(worklog)
    return worklog


def create_test_time_entry(
    session: Session,
    worklog: WorkLog,
    duration_minutes: int = 60,
) -> TimeEntry:
    """Create a test time entry."""
    start_time = datetime.utcnow() - timedelta(hours=2)
    end_time = start_time + timedelta(minutes=duration_minutes)

    entry = TimeEntry(
        work_log_id=worklog.id,
        start_time=start_time,
        end_time=end_time,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


class TestPaymentPreview:
    """Tests for POST /payments/preview endpoint."""

    def test_payment_preview_valid(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test payment preview with valid worklogs."""
        freelancer = create_test_freelancer(db, "Preview Test", Decimal("60.00"))
        worklog1 = create_test_worklog(db, freelancer, "Task 1", WorkLogStatus.PENDING)
        worklog2 = create_test_worklog(db, freelancer, "Task 2", WorkLogStatus.APPROVED)
        create_test_time_entry(db, worklog1, duration_minutes=60)  # $60
        create_test_time_entry(db, worklog2, duration_minutes=120)  # $120

        response = client.post(
            f"{settings.API_V1_STR}/payments/preview",
            headers=superuser_token_headers,
            json=[str(worklog1.id), str(worklog2.id)],
        )
        assert response.status_code == 200
        data = response.json()

        assert data["total_worklogs"] == 2
        assert float(data["total_amount"]) == pytest.approx(180.00, rel=0.01)
        assert len(data["freelancer_breakdown"]) == 1
        assert data["freelancer_breakdown"][0]["freelancer_name"] == "Preview Test"
        assert data["can_process"] is True

    def test_payment_preview_already_paid(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test payment preview with already paid worklog."""
        freelancer = create_test_freelancer(db, "Already Paid Test")
        paid_worklog = create_test_worklog(db, freelancer, "Paid Task", WorkLogStatus.PAID)
        create_test_time_entry(db, paid_worklog)

        response = client.post(
            f"{settings.API_V1_STR}/payments/preview",
            headers=superuser_token_headers,
            json=[str(paid_worklog.id)],
        )
        assert response.status_code == 200
        data = response.json()

        assert data["total_worklogs"] == 0
        assert len(data["issues"]) > 0
        assert any(i["issue_type"] == "ALREADY_PAID" for i in data["issues"])
        assert data["can_process"] is False

    def test_payment_preview_zero_duration_warning(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test payment preview with zero duration worklog shows warning."""
        freelancer = create_test_freelancer(db, "Zero Duration Test")
        worklog = create_test_worklog(db, freelancer, "Empty Task", WorkLogStatus.PENDING)
        # No time entries added

        response = client.post(
            f"{settings.API_V1_STR}/payments/preview",
            headers=superuser_token_headers,
            json=[str(worklog.id)],
        )
        assert response.status_code == 200
        data = response.json()

        assert any(i["issue_type"] == "ZERO_DURATION" for i in data["issues"])
        # Should still be processable (it's a warning, not error)
        assert data["can_process"] is True

    def test_payment_preview_empty_list(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test payment preview with empty worklog list."""
        response = client.post(
            f"{settings.API_V1_STR}/payments/preview",
            headers=superuser_token_headers,
            json=[],
        )
        assert response.status_code == 400


class TestPaymentProcess:
    """Tests for POST /payments/process endpoint."""

    def test_process_payment_success(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test successful payment processing."""
        freelancer = create_test_freelancer(db, "Process Test", Decimal("50.00"))
        worklog = create_test_worklog(db, freelancer, "Process Task", WorkLogStatus.APPROVED)
        create_test_time_entry(db, worklog, duration_minutes=120)  # 2 hours = $100

        response = client.post(
            f"{settings.API_V1_STR}/payments/process",
            headers=superuser_token_headers,
            json={"worklog_ids": [str(worklog.id)], "notes": "Test payment"},
        )
        assert response.status_code == 200
        data = response.json()

        assert "batch_id" in data
        assert data["total_worklogs"] == 1
        assert float(data["total_amount"]) == pytest.approx(100.00, rel=0.01)
        assert data["status"] == "completed"

        # Verify worklog is now PAID
        db.refresh(worklog)
        assert worklog.status == WorkLogStatus.PAID
        assert worklog.payment_batch_id is not None

    def test_process_payment_multiple_freelancers(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test payment processing with multiple freelancers."""
        freelancer1 = create_test_freelancer(db, "Multi Process 1", Decimal("50.00"))
        freelancer2 = create_test_freelancer(db, "Multi Process 2", Decimal("75.00"))

        worklog1 = create_test_worklog(db, freelancer1, "Task F1", WorkLogStatus.APPROVED)
        worklog2 = create_test_worklog(db, freelancer2, "Task F2", WorkLogStatus.APPROVED)

        create_test_time_entry(db, worklog1, duration_minutes=60)  # $50
        create_test_time_entry(db, worklog2, duration_minutes=60)  # $75

        response = client.post(
            f"{settings.API_V1_STR}/payments/process",
            headers=superuser_token_headers,
            json={"worklog_ids": [str(worklog1.id), str(worklog2.id)]},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["total_worklogs"] == 2
        assert float(data["total_amount"]) == pytest.approx(125.00, rel=0.01)

    def test_process_payment_cannot_pay_already_paid(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test that already paid worklogs cannot be paid again."""
        freelancer = create_test_freelancer(db, "Double Pay Test")
        worklog = create_test_worklog(db, freelancer, "Double Pay Task", WorkLogStatus.PAID)
        create_test_time_entry(db, worklog)

        response = client.post(
            f"{settings.API_V1_STR}/payments/process",
            headers=superuser_token_headers,
            json={"worklog_ids": [str(worklog.id)]},
        )
        assert response.status_code == 400


class TestPaymentBatches:
    """Tests for GET /payments/batches endpoint."""

    def test_get_payment_batches(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test getting payment batch history."""
        # Create a payment to have history
        freelancer = create_test_freelancer(db, "Batch History Test")
        worklog = create_test_worklog(db, freelancer, "Batch Task", WorkLogStatus.APPROVED)
        create_test_time_entry(db, worklog)

        # Process a payment
        client.post(
            f"{settings.API_V1_STR}/payments/process",
            headers=superuser_token_headers,
            json={"worklog_ids": [str(worklog.id)]},
        )

        # Get batches
        response = client.get(
            f"{settings.API_V1_STR}/payments/batches",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "count" in data
        assert data["count"] >= 1
