"""Tests for worklog API endpoints."""
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


class TestWorklogsSummary:
    """Tests for GET /worklogs/summary endpoint."""

    def test_get_worklogs_summary_empty(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test getting worklogs summary when empty."""
        response = client.get(
            f"{settings.API_V1_STR}/worklogs/summary",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data

    def test_get_worklogs_summary_with_data(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test getting worklogs summary with data."""
        # Create test data
        freelancer = create_test_freelancer(db, "Summary Test", Decimal("75.00"))
        worklog = create_test_worklog(db, freelancer, "Test Task for Summary")
        create_test_time_entry(db, worklog, duration_minutes=90)  # 1.5 hours

        response = client.get(
            f"{settings.API_V1_STR}/worklogs/summary",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Find our test worklog
        test_worklog = next(
            (w for w in data["data"] if w["id"] == str(worklog.id)), None
        )
        assert test_worklog is not None
        assert test_worklog["freelancer_name"] == "Summary Test"
        assert test_worklog["total_duration_minutes"] == 90
        # 1.5 hours * $75/hr = $112.50
        assert float(test_worklog["total_amount"]) == pytest.approx(112.50, rel=0.01)

    def test_get_worklogs_summary_filter_by_status(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test filtering worklogs by status."""
        freelancer = create_test_freelancer(db, "Status Filter Test")
        pending_worklog = create_test_worklog(db, freelancer, "Pending Task", WorkLogStatus.PENDING)
        approved_worklog = create_test_worklog(db, freelancer, "Approved Task", WorkLogStatus.APPROVED)

        # Filter by pending only
        response = client.get(
            f"{settings.API_V1_STR}/worklogs/summary?status=pending",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        data = response.json()

        pending_ids = [w["id"] for w in data["data"]]
        assert str(pending_worklog.id) in pending_ids


class TestWorklogDetail:
    """Tests for GET /worklogs/{id}/detail endpoint."""

    def test_get_worklog_detail(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test getting worklog detail with time entries."""
        freelancer = create_test_freelancer(db, "Detail Test", Decimal("100.00"))
        worklog = create_test_worklog(db, freelancer, "Detail Test Task")
        entry1 = create_test_time_entry(db, worklog, duration_minutes=60)
        entry2 = create_test_time_entry(db, worklog, duration_minutes=30)

        response = client.get(
            f"{settings.API_V1_STR}/worklogs/{worklog.id}/detail",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["task_description"] == "Detail Test Task"
        assert len(data["time_entries"]) == 2
        assert data["total_duration_minutes"] == 90
        # 1.5 hours * $100/hr = $150
        assert float(data["total_amount"]) == pytest.approx(150.00, rel=0.01)
        assert data["freelancer"]["name"] == "Detail Test"

    def test_get_worklog_detail_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test getting non-existent worklog."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"{settings.API_V1_STR}/worklogs/{fake_id}/detail",
            headers=superuser_token_headers,
        )
        assert response.status_code == 404


class TestWorklogStatusTransition:
    """Tests for PATCH /worklogs/{id}/status endpoint."""

    def test_valid_status_transition_pending_to_approved(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test valid transition from PENDING to APPROVED."""
        freelancer = create_test_freelancer(db, "Transition Test")
        worklog = create_test_worklog(db, freelancer, "Transition Task", WorkLogStatus.PENDING)

        response = client.patch(
            f"{settings.API_V1_STR}/worklogs/{worklog.id}/status?status=approved",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    def test_invalid_status_transition_paid_to_pending(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test invalid transition from PAID (should fail)."""
        freelancer = create_test_freelancer(db, "Invalid Transition Test")
        worklog = create_test_worklog(db, freelancer, "Paid Task", WorkLogStatus.PAID)

        response = client.patch(
            f"{settings.API_V1_STR}/worklogs/{worklog.id}/status?status=pending",
            headers=superuser_token_headers,
        )
        assert response.status_code == 400
        assert "Cannot transition" in response.json()["detail"]


class TestPaymentCalculations:
    """Tests for payment calculation accuracy."""

    @pytest.mark.parametrize(
        "duration_minutes,hourly_rate,expected_amount",
        [
            (60, Decimal("50.00"), 50.00),      # 1 hour
            (90, Decimal("50.00"), 75.00),      # 1.5 hours
            (30, Decimal("100.00"), 50.00),     # 0.5 hours
            (120, Decimal("75.00"), 150.00),    # 2 hours
            (45, Decimal("80.00"), 60.00),      # 0.75 hours
        ],
    )
    def test_payment_amount_calculation(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
        duration_minutes: int,
        hourly_rate: Decimal,
        expected_amount: float,
    ) -> None:
        """Test that payment amounts are calculated correctly."""
        freelancer = create_test_freelancer(
            db, f"Calc Test {duration_minutes}", hourly_rate
        )
        worklog = create_test_worklog(db, freelancer, f"Calc Task {duration_minutes}")
        create_test_time_entry(db, worklog, duration_minutes=duration_minutes)

        response = client.get(
            f"{settings.API_V1_STR}/worklogs/{worklog.id}/detail",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert float(data["total_amount"]) == pytest.approx(expected_amount, rel=0.01)
