import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal

from sqlmodel import Session, select

from app.core.db import engine
from app.core.config import settings
from app.models import User, WorkLog, WorkLogSegment, WorkLogAdjustment


def seed() -> None:
    with Session(engine) as session:
        # Get the superuser created during prestart
        user = session.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
        if not user:
            raise RuntimeError("Superuser not found. Ensure initial_data ran.")

        # If worklogs already exist for this user, skip
        existing = session.exec(select(WorkLog).where(WorkLog.user_id == user.id)).all()
        if existing:
            print("WorkLogs already present; skipping seed.")
            return

        # Create a sample WorkLog
        wl = WorkLog(
            user_id=user.id,
            task_name="January feature work",
            description="Implementation of new features",
            created_at=datetime.utcnow(),
            total_remitted_amount=Decimal("0.00"),
        )
        session.add(wl)
        session.flush()

        # Add two segments: 5h at $80/h and 3h at $50/h
        now = datetime.utcnow()
        seg1 = WorkLogSegment(
            worklog_id=wl.id,
            start_time=now - timedelta(hours=8),
            end_time=now - timedelta(hours=3),
            hourly_rate=Decimal("80.00"),
            is_active=True,
            created_at=now - timedelta(hours=8),
        )
        seg2 = WorkLogSegment(
            worklog_id=wl.id,
            start_time=now - timedelta(hours=5),
            end_time=now - timedelta(hours=2),
            hourly_rate=Decimal("50.00"),
            is_active=True,
            created_at=now - timedelta(hours=5),
        )

        session.add(seg1)
        session.add(seg2)

        # Add an adjustment: -$40 deduction
        adj = WorkLogAdjustment(
            worklog_id=wl.id,
            amount=Decimal("-40.00"),
            reason="Quality issue correction",
            created_at=datetime.utcnow(),
        )
        session.add(adj)

        session.commit()
        print("Seeded sample WorkLog, segments, and adjustment.")


if __name__ == "__main__":
    seed()