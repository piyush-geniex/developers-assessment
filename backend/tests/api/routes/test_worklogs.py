import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import (
    Remittance,
    User,
    UserCreate,
    WorkLog,
    WorkLogAdjustment,
    WorkLogSegment,
)
from tests.utils.utils import random_email, random_lower_string


def _get_user_by_email(db: Session, email: str) -> User:
    user = crud.get_user_by_email(session=db, email=email)
    assert user is not None
    return user


def test_create_worklog_requires_superuser(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    superuser = _get_user_by_email(db, settings.FIRST_SUPERUSER)
    data = {
        "user_id": str(superuser.id),
        "task_code": "TASK-001",
        "description": "Normal user should not be allowed",
    }

    response = client.post(
        f"{settings.API_V1_STR}/worklogs",
        headers=normal_user_token_headers,
        json=data,
    )

    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "The user doesn't have enough privileges"


def test_create_worklog_and_helpers(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    worklog_data = {
        "user_id": str(user.id),
        "task_code": "TASK-100",
        "description": "Settlement flow test",
    }
    worklog_response = client.post(
        f"{settings.API_V1_STR}/worklogs",
        headers=superuser_token_headers,
        json=worklog_data,
    )

    assert worklog_response.status_code == 200
    worklog_content = worklog_response.json()
    assert worklog_content["user_id"] == str(user.id)
    assert worklog_content["task_code"] == worklog_data["task_code"]
    worklog_id = worklog_content["id"]

    segment_data = {
        "worklog_id": worklog_id,
        "work_date": "2025-01-10",
        "hours": 8,
        "hourly_rate": 100,
        "is_questioned": False,
    }
    segment_response = client.post(
        f"{settings.API_V1_STR}/worklogs/segments",
        headers=superuser_token_headers,
        json=segment_data,
    )

    assert segment_response.status_code == 200
    segment_content = segment_response.json()
    assert segment_content["worklog_id"] == worklog_id
    assert segment_content["is_questioned"] is False

    adjustment_data = {
        "worklog_id": worklog_id,
        "segment_id": None,
        "amount": 50,
        "reason": "Bonus payment",
        "effective_date": "2025-01-20",
    }
    adjustment_response = client.post(
        f"{settings.API_V1_STR}/worklogs/adjustments",
        headers=superuser_token_headers,
        json=adjustment_data,
    )

    assert adjustment_response.status_code == 200
    adjustment_content = adjustment_response.json()
    assert adjustment_content["worklog_id"] == worklog_id
    assert Decimal(str(adjustment_content["amount"])) == Decimal("50")


def test_create_worklog_segment_and_adjustment_validation_errors(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    missing_worklog_segment_data = {
        "worklog_id": str(uuid.uuid4()),
        "work_date": "2025-01-10",
        "hours": 8,
        "hourly_rate": 100,
        "is_questioned": False,
    }
    segment_response = client.post(
        f"{settings.API_V1_STR}/worklogs/segments",
        headers=superuser_token_headers,
        json=missing_worklog_segment_data,
    )
    assert segment_response.status_code == 404
    assert segment_response.json()["detail"] == "WorkLog not found"

    missing_worklog_adjustment_data = {
        "worklog_id": str(uuid.uuid4()),
        "segment_id": None,
        "amount": 10,
        "reason": "Should fail",
        "effective_date": "2025-01-10",
    }
    adjustment_response = client.post(
        f"{settings.API_V1_STR}/worklogs/adjustments",
        headers=superuser_token_headers,
        json=missing_worklog_adjustment_data,
    )
    assert adjustment_response.status_code == 404
    assert adjustment_response.json()["detail"] == "WorkLog not found"


def test_create_worklog_adjustment_invalid_segment_for_worklog(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    other_worklog = WorkLog(user_id=user.id)
    db.add(other_worklog)
    db.commit()
    db.refresh(other_worklog)

    unrelated_segment = WorkLogSegment(
        worklog_id=other_worklog.id,
        work_date="2025-01-05",
        hours=4,
        hourly_rate=100,
    )
    db.add(unrelated_segment)
    db.commit()
    db.refresh(unrelated_segment)

    another_worklog = WorkLog(user_id=user.id)
    db.add(another_worklog)
    db.commit()
    db.refresh(another_worklog)

    adjustment_data = {
        "worklog_id": str(another_worklog.id),
        "segment_id": str(unrelated_segment.id),
        "amount": 10,
        "reason": "Segment does not belong to worklog",
        "effective_date": "2025-01-10",
    }
    response = client.post(
        f"{settings.API_V1_STR}/worklogs/adjustments",
        headers=superuser_token_headers,
        json=adjustment_data,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Segment does not belong to the specified WorkLog"
    )


def test_generate_remittances_and_list_all_worklogs_flow(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    worklog_data = {
        "user_id": str(user.id),
        "task_code": "TASK-200",
        "description": "End-to-end settlement flow",
    }
    worklog_response = client.post(
        f"{settings.API_V1_STR}/worklogs",
        headers=superuser_token_headers,
        json=worklog_data,
    )
    assert worklog_response.status_code == 200
    worklog = worklog_response.json()
    worklog_id = worklog["id"]

    first_segment_data = {
        "worklog_id": worklog_id,
        "work_date": "2025-01-10",
        "hours": 8,
        "hourly_rate": 100,
        "is_questioned": False,
    }
    first_segment_response = client.post(
        f"{settings.API_V1_STR}/worklogs/segments",
        headers=superuser_token_headers,
        json=first_segment_data,
    )
    assert first_segment_response.status_code == 200
    first_segment = first_segment_response.json()

    questioned_segment_data = {
        "worklog_id": worklog_id,
        "work_date": "2025-01-15",
        "hours": 4,
        "hourly_rate": 100,
        "is_questioned": True,
    }
    questioned_segment_response = client.post(
        f"{settings.API_V1_STR}/worklogs/segments",
        headers=superuser_token_headers,
        json=questioned_segment_data,
    )
    assert questioned_segment_response.status_code == 200

    adjustment_data = {
        "worklog_id": worklog_id,
        "segment_id": None,
        "amount": 50,
        "reason": "Bonus after review",
        "effective_date": "2025-01-20",
    }
    adjustment_response = client.post(
        f"{settings.API_V1_STR}/worklogs/adjustments",
        headers=superuser_token_headers,
        json=adjustment_data,
    )
    assert adjustment_response.status_code == 200

    list_response = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs",
        headers=superuser_token_headers,
    )
    assert list_response.status_code == 200
    list_content = list_response.json()

    target_summary = None
    for summary in list_content["data"]:
        if summary["worklog_id"] == worklog_id:
            target_summary = summary
            break

    assert target_summary is not None
    assert target_summary["remittance_status"] == "UNREMITTED"
    assert Decimal(str(target_summary["total_amount"])) == Decimal("850")

    list_unremitted_response = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs?remittanceStatus=UNREMITTED",
        headers=superuser_token_headers,
    )
    assert list_unremitted_response.status_code == 200
    list_unremitted_content = list_unremitted_response.json()
    assert any(
        summary["worklog_id"] == worklog_id
        for summary in list_unremitted_content["data"]
    )

    list_remitted_response = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs?remittanceStatus=REMITTED",
        headers=superuser_token_headers,
    )
    assert list_remitted_response.status_code == 200
    list_remitted_content = list_remitted_response.json()
    assert all(
        summary["worklog_id"] != worklog_id
        for summary in list_remitted_content["data"]
    )

    generate_body = {
        "period_start": "2025-01-01",
        "period_end": "2025-01-31",
    }
    generate_response = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        headers=superuser_token_headers,
        json=generate_body,
    )

    assert generate_response.status_code == 200
    generate_content = generate_response.json()

    assert len(generate_content["remittances"]) >= 1
    user_summary = None
    for remittance_summary in generate_content["remittances"]:
        if remittance_summary["user_id"] == str(user.id):
            user_summary = remittance_summary
            break

    assert user_summary is not None
    assert user_summary["period_start"] == generate_body["period_start"]
    assert user_summary["period_end"] == generate_body["period_end"]
    assert Decimal(str(user_summary["total_amount"])) == Decimal("850")

    remittances_query = select(Remittance).where(Remittance.user_id == user.id)
    remittances = db.exec(remittances_query).all()
    assert len(remittances) >= 1

    segments_query = select(WorkLogSegment).where(
        WorkLogSegment.worklog_id == uuid.UUID(worklog_id)
    )
    segments = db.exec(segments_query).all()
    assert len(segments) == 2

    for segment in segments:
        if segment.id == uuid.UUID(first_segment["id"]):
            assert segment.is_settled is True
        if segment.is_questioned:
            assert segment.is_settled is False

    adjustments_query = select(WorkLogAdjustment).where(
        WorkLogAdjustment.worklog_id == uuid.UUID(worklog_id)
    )
    adjustments = db.exec(adjustments_query).all()
    assert len(adjustments) == 1
    assert adjustments[0].is_settled is True

    list_after_response = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs?remittanceStatus=REMITTED",
        headers=superuser_token_headers,
    )
    assert list_after_response.status_code == 200
    list_after_content = list_after_response.json()

    remitted_summary = None
    for summary in list_after_content["data"]:
        if summary["worklog_id"] == worklog_id:
            remitted_summary = summary
            break

    assert remitted_summary is not None
    assert remitted_summary["remittance_status"] == "REMITTED"
    assert Decimal(str(remitted_summary["total_amount"])) == Decimal("850")

    list_unremitted_after_response = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs?remittanceStatus=UNREMITTED",
        headers=superuser_token_headers,
    )
    assert list_unremitted_after_response.status_code == 200
    list_unremitted_after_content = list_unremitted_after_response.json()
    assert all(
        summary["worklog_id"] != worklog_id
        for summary in list_unremitted_after_content["data"]
    )


def test_list_all_worklogs_invalid_remittance_status(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs?remittanceStatus=INVALID",
        headers=superuser_token_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid remittanceStatus value"


def test_generate_remittances_invalid_period(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    body = {
        "period_start": "2025-02-01",
        "period_end": "2025-01-01",
    }
    response = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        headers=superuser_token_headers,
        json=body,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "period_start must be before period_end"
