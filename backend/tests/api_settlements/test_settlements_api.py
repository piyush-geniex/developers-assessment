"""
Integration tests for settlement API endpoints.

Tests both required endpoints:
- POST /generate-remittances-for-all-users
- GET /list-all-worklogs
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.db import engine
from app.main import app
from app.models import (
    Adjustment,
    AdjustmentType,
    Remittance,
    RemittanceStatus,
    TimeSegment,
    User,
    WorkLog,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_session():
    """Create test session."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_user(test_session: Session) -> User:
    """Get or create test user."""
    user = test_session.exec(select(User).limit(1)).first()
    if user:
        return user

    user = User(
        email="api_test@example.com",
        hashed_password="dummy",
        is_active=True, is_superuser=False,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


def test_generate_remittances_success(client: TestClient, test_session: Session, test_user: User):
    """Test successful remittance generation."""
    # Create worklog with time segments
    worklog = WorkLog(
        worker_user_id=test_user.id,
        task_identifier="API-TEST-001",
    )
    test_session.add(worklog)
    test_session.flush()

    segment = TimeSegment(
        worklog_id=worklog.id,
        hours_worked=Decimal("10.00"),
        hourly_rate=Decimal("50.00"),
        segment_date=date.today(),
    )
    test_session.add(segment)
    test_session.commit()

    # Call API
    response = client.post(
        "/api/v1/generate-remittances-for-all-users",
        params={
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["remittances_created"] >= 1
    assert Decimal(data["total_gross_amount"]) >= Decimal("500.00")
    assert "settlement" in data
    assert data["settlement"]["status"] == "COMPLETED"


def test_generate_remittances_invalid_dates(client: TestClient):
    """Test that invalid date range returns 400."""
    response = client.post(
        "/api/v1/generate-remittances-for-all-users",
        params={
            "period_start": str(date.today()),
            "period_end": str(date.today() - timedelta(days=1)),  # Invalid!
        },
    )

    assert response.status_code == 400
    assert "period_start must be <= period_end" in response.json()["detail"]


def test_list_worklogs_no_filter(client: TestClient, test_session: Session, test_user: User):
    """Test listing all worklogs without filter."""
    # Create worklog
    worklog = WorkLog(
        worker_user_id=test_user.id,
        task_identifier="API-TEST-LIST",
    )
    test_session.add(worklog)
    test_session.flush()

    segment = TimeSegment(
        worklog_id=worklog.id,
        hours_worked=Decimal("5.00"),
        hourly_rate=Decimal("40.00"),
        segment_date=date.today(),
    )
    test_session.add(segment)
    test_session.commit()

    # Call API
    response = client.get("/api/v1/list-all-worklogs")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "count" in data
    assert data["count"] >= 1


def test_list_worklogs_filter_unremitted(client: TestClient, test_session: Session, test_user: User):
    """Test filtering by UNREMITTED status."""
    # Create unremitted worklog
    worklog = WorkLog(
        worker_user_id=test_user.id,
        task_identifier="API-TEST-UNREMITTED",
    )
    test_session.add(worklog)
    test_session.flush()

    segment = TimeSegment(
        worklog_id=worklog.id,
        hours_worked=Decimal("3.00"),
        hourly_rate=Decimal("60.00"),
        segment_date=date.today(),
    )
    test_session.add(segment)
    test_session.commit()

    # Call API with filter
    response = client.get(
        "/api/v1/list-all-worklogs",
        params={"remittanceStatus": "UNREMITTED"},
    )

    assert response.status_code == 200
    data = response.json()

    # All returned worklogs should be unremitted
    for worklog_data in data["data"]:
        assert worklog_data["is_remitted"] == False


def test_list_worklogs_pagination(client: TestClient, test_session: Session, test_user: User):
    """Test pagination parameters."""
    # Create multiple worklogs
    for i in range(5):
        worklog = WorkLog(
            worker_user_id=test_user.id,
            task_identifier=f"API-TEST-PAGE-{i}",
        )
        test_session.add(worklog)
        test_session.flush()

        segment = TimeSegment(
            worklog_id=worklog.id,
            hours_worked=Decimal("1.00"),
            hourly_rate=Decimal("50.00"),
            segment_date=date.today(),
        )
        test_session.add(segment)

    test_session.commit()

    # Test pagination
    response = client.get(
        "/api/v1/list-all-worklogs",
        params={"skip": 0, "limit": 2},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["data"]) <= 2


def test_list_worklogs_amount_calculation(client: TestClient, test_session: Session, test_user: User):
    """Test that amount is calculated correctly for each worklog."""
    # Create worklog with multiple segments
    worklog = WorkLog(
        worker_user_id=test_user.id,
        task_identifier="API-TEST-AMOUNT",
    )
    test_session.add(worklog)
    test_session.flush()

    # Add 2 segments
    segments = [
        TimeSegment(
            worklog_id=worklog.id,
            hours_worked=Decimal("5.00"),
            hourly_rate=Decimal("50.00"),
            segment_date=date.today(),
        ),
        TimeSegment(
            worklog_id=worklog.id,
            hours_worked=Decimal("3.00"),
            hourly_rate=Decimal("60.00"),
            segment_date=date.today() + timedelta(days=1),
        ),
    ]
    for segment in segments:
        test_session.add(segment)

    # Add adjustment
    adjustment = Adjustment(
        worklog_id=worklog.id,
        adjustment_type=AdjustmentType.DEDUCTION,
        amount=Decimal("50.00"),
        reason="Test deduction",
    )
    test_session.add(adjustment)
    test_session.commit()

    # Call API
    response = client.get("/api/v1/list-all-worklogs")

    assert response.status_code == 200
    data = response.json()

    # Find our worklog
    our_worklog = next(
        (wl for wl in data["data"] if wl["task_identifier"] == "API-TEST-AMOUNT"),
        None,
    )

    assert our_worklog is not None
    # Expected: (5*50) + (3*60) - 50 = 250 + 180 - 50 = 380
    assert Decimal(our_worklog["total_amount"]) == Decimal("380.00")


def test_generate_remittances_default_period_end(client: TestClient):
    """Test that period_end defaults to  today when not provided."""
    response = client.post(
        "/api/v1/generate-remittances-for-all-users",
        params={"period_start": str(date.today() - timedelta(days=7))},
    )

    # Should default to today and succeed
    assert response.status_code == 200
