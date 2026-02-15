from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import (
    Remittance,
    RemittanceLine,
    User,
    UserCreate,
    Worklog,
    WorklogEntry,
    WorklogEntryType,
    WorklogRemittanceStatus,
)
from tests.utils.utils import random_email


def _mk_user(db: Session) -> User:
    return crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password="simplepass123"),
    )


def _mk_worklog(db: Session, user_id, task_ref: str) -> Worklog:
    wl = Worklog(user_id=user_id, task_ref=task_ref)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return wl


def _mk_entry(
    db: Session,
    worklog_id: int,
    amount: Decimal,
    occurred_at: datetime,
    entry_type: str = WorklogEntryType.TIME_SEGMENT,
) -> WorklogEntry:
    ent = WorklogEntry(
        worklog_id=worklog_id,
        entry_type=entry_type,
        amount_signed=amount,
        occurred_at=occurred_at,
    )
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent


def _payload(run_key: str) -> dict[str, str]:
    return {
        "from_date": "2026-01-01",
        "to_date": "2026-01-31",
        "idempotency_key": run_key,
    }


def _run_settlement(
    client: TestClient, run_key: str, payout_mode: str | None = None
) -> dict:
    headers = {"X-Payout-Mode": payout_mode} if payout_mode else None
    resp = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        json=_payload(run_key),
        headers=headers,
    )
    assert resp.status_code == 200
    return resp.json()


def test_generate_remittances_basic_strict_period_success(
    client: TestClient, db: Session
) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-basic-success-1")
    _mk_entry(
        db, wl.id or 0, Decimal("100.00"), occurred_at=datetime(2026, 1, 15, 9, 0, 0)
    )

    content = _run_settlement(client, "tc1_run_001", payout_mode="success")
    assert content["run_status"] == "COMPLETED"
    assert content["remitted_count"] >= 1
    assert content["failed_count"] == 0
    assert content["cancelled_count"] == 0


def test_generate_remittances_idempotent(client: TestClient, db: Session) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-idempotent-1")
    _mk_entry(
        db, wl.id or 0, Decimal("100.00"), occurred_at=datetime(2026, 1, 15, 9, 0, 0)
    )

    key = "run_key_001"
    resp_1 = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        json=_payload(key),
    )
    assert resp_1.status_code == 200
    c1 = resp_1.json()
    assert c1["idempotency_key"] == key
    assert c1["remitted_count"] == 1

    resp_2 = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        json=_payload(key),
    )
    assert resp_2.status_code == 200
    c2 = resp_2.json()
    assert c2["run_id"] == c1["run_id"]
    assert c2["remitted_count"] == 1

    rems = db.exec(
        select(Remittance).where(
            Remittance.idempotency_key == key, Remittance.user_id == usr.id
        )
    ).all()
    assert len(rems) == 1


def test_generate_remittances_work_evolves_delta_only(
    client: TestClient, db: Session
) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-work-evolves-1")
    _mk_entry(
        db, wl.id or 0, Decimal("100.00"), occurred_at=datetime(2026, 1, 9, 10, 0, 0)
    )
    first = _run_settlement(client, "tc3_run_001", payout_mode="success")
    assert first["run_status"] == "COMPLETED"
    assert first["remitted_count"] >= 1

    _mk_entry(
        db, wl.id or 0, Decimal("20.00"), occurred_at=datetime(2026, 1, 20, 10, 0, 0)
    )
    second = _run_settlement(client, "tc3_run_002", payout_mode="success")
    rows = [x for x in second["results"] if x["user_id"] == str(usr.id)]
    assert rows
    assert rows[0]["status"] == "REMITTED"
    assert rows[0]["amount"] == "20.00"


def test_generate_remittances_retroactive_adjustment_negative_after_settlement(
    client: TestClient, db: Session
) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-retro-adjust-1")
    _mk_entry(
        db, wl.id or 0, Decimal("50.00"), occurred_at=datetime(2026, 1, 7, 9, 0, 0)
    )
    first = _run_settlement(client, "tc4_run_001", payout_mode="success")
    assert first["remitted_count"] >= 1

    _mk_entry(
        db,
        wl.id or 0,
        Decimal("-50.00"),
        occurred_at=datetime(2026, 1, 22, 11, 0, 0),
        entry_type=WorklogEntryType.ADJUSTMENT,
    )
    second = _run_settlement(client, "tc4_run_002", payout_mode="success")
    rows = [x for x in second["results"] if x["user_id"] == str(usr.id)]
    assert rows
    assert rows[0]["status"] == "SKIPPED_NEGATIVE"
    assert rows[0]["amount"] == "-50.00"


def test_generate_remittances_simulated_failure_path(
    client: TestClient, db: Session
) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-fail-path-1")
    _mk_entry(
        db, wl.id or 0, Decimal("70.00"), occurred_at=datetime(2026, 1, 12, 10, 0, 0)
    )

    failed = _run_settlement(client, "tc5_run_fail_001", payout_mode="fail")
    rows = [x for x in failed["results"] if x["user_id"] == str(usr.id)]
    assert rows
    assert rows[0]["status"] == "FAILED"
    assert failed["run_status"] == "PARTIAL_SUCCESS"

    retry = _run_settlement(client, "tc5_run_success_002", payout_mode="success")
    retry_rows = [x for x in retry["results"] if x["user_id"] == str(usr.id)]
    assert retry_rows
    assert retry_rows[0]["status"] == "REMITTED"
    assert retry_rows[0]["amount"] == "70.00"


def test_generate_remittances_fail_and_retry_in_next_run(
    client: TestClient, db: Session
) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-fail-then-success")
    _mk_entry(
        db, wl.id or 0, Decimal("50.00"), occurred_at=datetime(2026, 1, 11, 10, 0, 0)
    )

    resp = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        json=_payload("run_key_002"),
        headers={"X-Payout-Mode": "fail"},
    )

    assert resp.status_code == 200
    content = resp.json()
    assert content["run_status"] == "PARTIAL_SUCCESS"
    assert content["remitted_count"] == 0
    assert content["failed_count"] == 1

    retry_resp = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        json=_payload("run_key_003"),
        headers={"X-Payout-Mode": "success"},
    )
    assert retry_resp.status_code == 200
    retry_content = retry_resp.json()
    assert retry_content["remitted_count"] >= 1


def test_generate_remittances_negative_balance(client: TestClient, db: Session) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-negative-1")
    _mk_entry(
        db,
        wl.id or 0,
        Decimal("-30.00"),
        occurred_at=datetime(2026, 1, 21, 11, 0, 0),
        entry_type=WorklogEntryType.ADJUSTMENT,
    )

    resp = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        json=_payload("run_key_004"),
    )
    assert resp.status_code == 200
    content = resp.json()
    assert content["skipped_negative_count"] >= 1
    sts = [x["status"] for x in content["results"] if x["user_id"] == str(usr.id)]
    assert "SKIPPED_NEGATIVE" in sts


def test_list_all_worklogs_filter(client: TestClient, db: Session) -> None:
    usr = _mk_user(db)
    wl_paid = _mk_worklog(db, usr.id, "t-list-1")
    _mk_entry(
        db,
        wl_paid.id or 0,
        Decimal("25.00"),
        occurred_at=datetime(2026, 1, 17, 8, 0, 0),
    )
    client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        json=_payload("run_key_005"),
    )

    wl_unpaid = _mk_worklog(db, usr.id, "t-list-2")
    _mk_entry(
        db,
        wl_unpaid.id or 0,
        Decimal("10.00"),
        occurred_at=datetime(2026, 2, 2, 12, 0, 0),
    )

    resp_all = client.get(f"{settings.API_V1_STR}/list-all-worklogs")
    assert resp_all.status_code == 200
    all_data = resp_all.json()["data"]
    ids = {x["worklog_id"] for x in all_data}
    assert (wl_paid.id or 0) in ids
    assert (wl_unpaid.id or 0) in ids

    resp_r = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs",
        params={"remittanceStatus": WorklogRemittanceStatus.REMITTED},
    )
    assert resp_r.status_code == 200
    remitted_ids = {x["worklog_id"] for x in resp_r.json()["data"]}
    assert (wl_paid.id or 0) in remitted_ids

    resp_u = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs",
        params={"remittanceStatus": WorklogRemittanceStatus.UNREMITTED},
    )
    assert resp_u.status_code == 200
    unremitted_ids = {x["worklog_id"] for x in resp_u.json()["data"]}
    assert (wl_unpaid.id or 0) in unremitted_ids

    resp_bad = client.get(
        f"{settings.API_V1_STR}/list-all-worklogs",
        params={"remittanceStatus": "BAD_VALUE"},
    )
    assert resp_bad.status_code == 400


def test_generate_remittances_strict_period_excludes_out_of_window(
    client: TestClient, db: Session
) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-period-1")
    _mk_entry(
        db, wl.id or 0, Decimal("20.00"), occurred_at=datetime(2026, 1, 10, 10, 0, 0)
    )
    _mk_entry(
        db, wl.id or 0, Decimal("30.00"), occurred_at=datetime(2026, 2, 10, 10, 0, 0)
    )

    resp = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        json={
            "from_date": "2026-01-01",
            "to_date": "2026-01-31",
            "idempotency_key": "run_key_006",
        },
        headers={"X-Payout-Mode": "success"},
    )
    assert resp.status_code == 200
    content = resp.json()
    usr_rows = [x for x in content["results"] if x["user_id"] == str(usr.id)]
    assert usr_rows
    assert usr_rows[0]["amount"] == "20.00"


def test_generate_remittances_cancel_mode(client: TestClient, db: Session) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-cancel-1")
    _mk_entry(
        db, wl.id or 0, Decimal("15.00"), occurred_at=datetime(2026, 1, 8, 10, 0, 0)
    )

    resp = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        json=_payload("run_key_007"),
        headers={"X-Payout-Mode": "cancel"},
    )
    assert resp.status_code == 200
    content = resp.json()
    assert content["cancelled_count"] >= 1
    rem_ids = db.exec(
        select(Remittance.id).where(
            Remittance.idempotency_key == "run_key_007", Remittance.user_id == usr.id
        )
    ).all()
    assert rem_ids
    ln_rows = db.exec(select(RemittanceLine).where(RemittanceLine.remittance_id.in_(rem_ids))).all()
    assert len(ln_rows) == 0


def test_generate_remittances_additional_segment_and_adjustment_sequence_delta(
    client: TestClient, db: Session
) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-seq-delta-1")
    _mk_entry(
        db, wl.id or 0, Decimal("100.00"), occurred_at=datetime(2026, 1, 6, 9, 0, 0)
    )
    first = _run_settlement(client, "tc10_run_initial_001", payout_mode="success")
    assert first["remitted_count"] >= 1

    _mk_entry(
        db, wl.id or 0, Decimal("30.00"), occurred_at=datetime(2026, 1, 18, 9, 0, 0)
    )
    _mk_entry(
        db,
        wl.id or 0,
        Decimal("-20.00"),
        occurred_at=datetime(2026, 1, 21, 9, 0, 0),
        entry_type=WorklogEntryType.ADJUSTMENT,
    )

    second = _run_settlement(client, "tc10_run_delta_002", payout_mode="success")
    rows = [x for x in second["results"] if x["user_id"] == str(usr.id)]
    assert rows
    assert rows[0]["status"] == "REMITTED"
    assert rows[0]["amount"] == "10.00"

    list_resp = client.get(f"{settings.API_V1_STR}/list-all-worklogs")
    assert list_resp.status_code == 200
    row = next(
        x for x in list_resp.json()["data"] if x["worklog_id"] == (wl.id or 0)
    )
    assert row["gross_amount"] == "110.00"
    assert row["remitted_amount"] == "110.00"
    assert row["unremitted_amount"] == "0.00"


def test_generate_remittances_previous_failed_succeeds_next_run_explicit(
    client: TestClient, db: Session
) -> None:
    usr = _mk_user(db)
    wl = _mk_worklog(db, usr.id, "t-fail-success-explicit-1")
    _mk_entry(
        db, wl.id or 0, Decimal("75.00"), occurred_at=datetime(2026, 1, 14, 8, 0, 0)
    )

    failed = _run_settlement(client, "tc11_run_fail_001", payout_mode="fail")
    fail_rows = [x for x in failed["results"] if x["user_id"] == str(usr.id)]
    assert fail_rows
    assert fail_rows[0]["status"] == "FAILED"

    success = _run_settlement(client, "tc11_run_success_002", payout_mode="success")
    ok_rows = [x for x in success["results"] if x["user_id"] == str(usr.id)]
    assert ok_rows
    assert ok_rows[0]["status"] == "REMITTED"
    assert ok_rows[0]["amount"] == "75.00"

    rems = db.exec(
        select(Remittance).where(
            Remittance.user_id == usr.id,
            Remittance.idempotency_key.in_(["tc11_run_fail_001", "tc11_run_success_002"]),
        )
    ).all()
    success_rems = [x for x in rems if x.status == "REMITTED"]
    assert len(success_rems) == 1
    assert str(success_rems[0].total_amount) == "75.00"
