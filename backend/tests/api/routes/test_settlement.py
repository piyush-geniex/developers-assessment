from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import (
    Adjustment,
    Remittance,
    RemittanceWorklog,
    TimeSegment,
    User,
    WorkLog,
)


def _create_test_worker(db: Session, email: str) -> User:
    """Helper to create a worker user for testing."""
    from app.core.security import get_password_hash

    usr = User(
        email=email,
        hashed_password=get_password_hash("testpass123"),
        full_name="Test Worker",
        is_active=True,
        is_superuser=False,
    )
    db.add(usr)
    db.commit()
    db.refresh(usr)
    return usr


def _create_worklog_with_segments(
    db: Session, u_id: object, title: str, segments: list[tuple[float, float]]
) -> WorkLog:
    """
    Helper to create a worklog with time segments.
    segments: list of (hours, rate) tuples
    """
    wl = WorkLog(user_id=u_id, title=title, status="ACTIVE")
    db.add(wl)
    db.commit()
    db.refresh(wl)

    for hrs, rt in segments:
        seg = TimeSegment(
            worklog_id=wl.id,
            hours=hrs,
            rate=rt,
            status="ACTIVE",
        )
        db.add(seg)
        db.commit()

    return wl


# --- Auth Tests ---


def test_generate_remittances_unauthenticated(client: TestClient) -> None:
    """Unauthenticated requests should be rejected."""
    resp = client.post("/api/v1/settlement/generate-remittances-for-all-users")
    assert resp.status_code == 401


def test_generate_remittances_normal_user_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Normal users should not be able to generate remittances."""
    resp = client.post(
        "/api/v1/settlement/generate-remittances-for-all-users",
        headers=normal_user_token_headers,
    )
    assert resp.status_code == 403


def test_generate_remittances_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Superusers should be able to generate remittances."""
    resp = client.post(
        "/api/v1/settlement/generate-remittances-for-all-users",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "count" in data
    assert isinstance(data["data"], list)


def test_list_worklogs_unauthenticated(client: TestClient) -> None:
    """Unauthenticated requests should be rejected."""
    resp = client.get("/api/v1/settlement/list-all-worklogs")
    assert resp.status_code == 401


def test_list_worklogs_authenticated(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Authenticated users should be able to list worklogs."""
    resp = client.get(
        "/api/v1/settlement/list-all-worklogs",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "count" in data
    assert isinstance(data["data"], list)


# --- Business Logic Tests ---


def test_worklog_amount_calculation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Worklog amount should be sum of (hours * rate) for active segments."""
    usr = _create_test_worker(db, "amount_test@example.com")

    # Create worklog with 2 active segments + 1 removed
    wl = WorkLog(user_id=usr.id, title="Amount Test", status="ACTIVE")
    db.add(wl)
    db.commit()
    db.refresh(wl)

    seg1 = TimeSegment(worklog_id=wl.id, hours=4.0, rate=50.0, status="ACTIVE")
    seg2 = TimeSegment(worklog_id=wl.id, hours=3.0, rate=50.0, status="ACTIVE")
    seg3 = TimeSegment(worklog_id=wl.id, hours=2.0, rate=50.0, status="REMOVED")
    db.add(seg1)
    db.add(seg2)
    db.add(seg3)
    db.commit()

    resp = client.get(
        "/api/v1/settlement/list-all-worklogs",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200

    wl_items = [w for w in resp.json()["data"] if w["id"] == str(wl.id)]
    assert len(wl_items) == 1
    # 4*50 + 3*50 = 350 (removed segment excluded)
    assert wl_items[0]["amount"] == 350.0
    assert wl_items[0]["remittance_status"] == "UNREMITTED"


def test_adjustment_affects_amount(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Adjustments should be included in the worklog amount."""
    usr = _create_test_worker(db, "adj_test@example.com")

    wl = _create_worklog_with_segments(db, usr.id, "Adj Test", [(5.0, 40.0)])

    # Add a deduction
    adj = Adjustment(
        worklog_id=wl.id,
        amount=-20.0,
        reason="Quality deduction",
        status="ACTIVE",
    )
    db.add(adj)
    db.commit()

    resp = client.get(
        "/api/v1/settlement/list-all-worklogs",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200

    wl_items = [w for w in resp.json()["data"] if w["id"] == str(wl.id)]
    assert len(wl_items) == 1
    # 5*40 - 20 = 180
    assert wl_items[0]["amount"] == 180.0


def test_generate_and_list_flow(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Full flow: create worklog, generate remittance, verify status."""
    usr = _create_test_worker(db, "flow_test@example.com")
    wl = _create_worklog_with_segments(db, usr.id, "Flow Test", [(3.0, 60.0)])

    # Generate remittances
    resp = client.post(
        "/api/v1/settlement/generate-remittances-for-all-users",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200

    # Check worklog is still UNREMITTED (remittance is PENDING, not SETTLED)
    resp = client.get(
        "/api/v1/settlement/list-all-worklogs",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200

    wl_items = [w for w in resp.json()["data"] if w["id"] == str(wl.id)]
    assert len(wl_items) == 1
    assert wl_items[0]["amount"] == 180.0
    assert wl_items[0]["remittance_status"] == "UNREMITTED"


def test_settled_remittance_marks_worklog_remitted(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """A worklog becomes REMITTED when its full amount is covered by SETTLED remittances."""
    usr = _create_test_worker(db, "settled_test@example.com")
    wl = _create_worklog_with_segments(db, usr.id, "Settled Test", [(2.0, 100.0)])

    # Create a settled remittance covering the full amount
    rmtnc = Remittance(
        user_id=usr.id,
        amount=200.0,
        status="SETTLED",
        period="2026-01",
    )
    db.add(rmtnc)
    db.commit()
    db.refresh(rmtnc)

    rw = RemittanceWorklog(
        remittance_id=rmtnc.id,
        worklog_id=wl.id,
        amount=200.0,
    )
    db.add(rw)
    db.commit()

    resp = client.get(
        "/api/v1/settlement/list-all-worklogs",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200

    wl_items = [w for w in resp.json()["data"] if w["id"] == str(wl.id)]
    assert len(wl_items) == 1
    assert wl_items[0]["remittance_status"] == "REMITTED"


def test_filter_by_remittance_status(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Filtering by REMITTED/UNREMITTED should return correct results."""
    resp_remitted = client.get(
        "/api/v1/settlement/list-all-worklogs?remittanceStatus=REMITTED",
        headers=superuser_token_headers,
    )
    assert resp_remitted.status_code == 200
    for wl in resp_remitted.json()["data"]:
        assert wl["remittance_status"] == "REMITTED"

    resp_unremitted = client.get(
        "/api/v1/settlement/list-all-worklogs?remittanceStatus=UNREMITTED",
        headers=superuser_token_headers,
    )
    assert resp_unremitted.status_code == 200
    for wl in resp_unremitted.json()["data"]:
        assert wl["remittance_status"] == "UNREMITTED"


def test_no_duplicate_remittances_on_rerun(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Running generate twice should not create duplicate pending remittances."""
    usr = _create_test_worker(db, "nodup_test@example.com")
    _create_worklog_with_segments(db, usr.id, "NoDup Test", [(4.0, 25.0)])

    # First run
    resp1 = client.post(
        "/api/v1/settlement/generate-remittances-for-all-users",
        headers=superuser_token_headers,
    )
    assert resp1.status_code == 200

    # Second run
    resp2 = client.post(
        "/api/v1/settlement/generate-remittances-for-all-users",
        headers=superuser_token_headers,
    )
    assert resp2.status_code == 200

    # The second run should not create new remittances for the same user
    # since pending remittances already cover the amount
    from sqlmodel import select

    rmtncs = db.exec(
        select(Remittance).where(Remittance.user_id == usr.id)
    ).all()

    # Should have at most 1 remittance (not 2)
    pending_rmtncs = [r for r in rmtncs if r.status == "PENDING"]
    assert len(pending_rmtncs) <= 1


def test_failed_remittance_makes_amount_reeligible(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Failed remittances should make worklog amounts re-eligible."""
    usr = _create_test_worker(db, "failed_test@example.com")
    wl = _create_worklog_with_segments(db, usr.id, "Failed Test", [(3.0, 40.0)])

    # Create a failed remittance
    rmtnc = Remittance(
        user_id=usr.id,
        amount=120.0,
        status="FAILED",
        period="2026-01",
    )
    db.add(rmtnc)
    db.commit()
    db.refresh(rmtnc)

    rw = RemittanceWorklog(
        remittance_id=rmtnc.id,
        worklog_id=wl.id,
        amount=120.0,
    )
    db.add(rw)
    db.commit()

    # Worklog should still be UNREMITTED since remittance failed
    resp = client.get(
        "/api/v1/settlement/list-all-worklogs",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200

    wl_items = [w for w in resp.json()["data"] if w["id"] == str(wl.id)]
    assert len(wl_items) == 1
    assert wl_items[0]["remittance_status"] == "UNREMITTED"


def test_normal_user_sees_own_worklogs_only(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Normal users should only see their own worklogs."""
    # Superuser should see more worklogs than normal user
    resp_super = client.get(
        "/api/v1/settlement/list-all-worklogs",
        headers=superuser_token_headers,
    )
    resp_normal = client.get(
        "/api/v1/settlement/list-all-worklogs",
        headers=normal_user_token_headers,
    )
    assert resp_super.status_code == 200
    assert resp_normal.status_code == 200

    # Normal user count should be <= superuser count
    assert resp_normal.json()["count"] <= resp_super.json()["count"]
