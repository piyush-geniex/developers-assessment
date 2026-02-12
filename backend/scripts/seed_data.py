import logging
import sys
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.db import engine
from app.core.security import get_password_hash
from app.models import (
    Adjustment,
    Remittance,
    RemittanceWorklog,
    TimeSegment,
    User,
    WorkLog,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed() -> None:
    with Session(engine) as session:
        # Check if seed data already exists
        existing_wls = session.exec(select(WorkLog)).first()
        if existing_wls:
            logger.info("Seed data already exists, skipping.")
            return

        # Create worker users for seeding
        u1 = session.exec(
            select(User).where(User.email == "worker1@example.com")
        ).first()
        if not u1:
            u1 = User(
                email="worker1@example.com",
                hashed_password=get_password_hash("worker1pass"),
                full_name="Alice Worker",
                is_active=True,
                is_superuser=False,
            )
            session.add(u1)
            session.commit()
            session.refresh(u1)

        u2 = session.exec(
            select(User).where(User.email == "worker2@example.com")
        ).first()
        if not u2:
            u2 = User(
                email="worker2@example.com",
                hashed_password=get_password_hash("worker2pass"),
                full_name="Bob Worker",
                is_active=True,
                is_superuser=False,
            )
            session.add(u2)
            session.commit()
            session.refresh(u2)

        logger.info(f"Seeding data for users: {u1.email}, {u2.email}")

        now = datetime.utcnow()

        # --- User 1: 2 worklogs ---

        wl1 = WorkLog(
            user_id=u1.id,
            title="API Integration Task",
            status="ACTIVE",
            created_at=now - timedelta(days=20),
        )
        session.add(wl1)
        session.commit()
        session.refresh(wl1)

        # Segments for worklog 1
        seg1 = TimeSegment(
            worklog_id=wl1.id,
            hours=4.0,
            rate=50.0,
            status="ACTIVE",
            created_at=now - timedelta(days=19),
        )
        seg2 = TimeSegment(
            worklog_id=wl1.id,
            hours=3.0,
            rate=50.0,
            status="ACTIVE",
            created_at=now - timedelta(days=18),
        )
        seg3 = TimeSegment(
            worklog_id=wl1.id,
            hours=2.0,
            rate=50.0,
            status="REMOVED",  # Removed segment
            created_at=now - timedelta(days=17),
        )
        session.add(seg1)
        session.add(seg2)
        session.add(seg3)
        session.commit()

        wl2 = WorkLog(
            user_id=u1.id,
            title="Database Migration Task",
            status="ACTIVE",
            created_at=now - timedelta(days=15),
        )
        session.add(wl2)
        session.commit()
        session.refresh(wl2)

        seg4 = TimeSegment(
            worklog_id=wl2.id,
            hours=6.0,
            rate=55.0,
            status="ACTIVE",
            created_at=now - timedelta(days=14),
        )
        seg5 = TimeSegment(
            worklog_id=wl2.id,
            hours=2.0,
            rate=55.0,
            status="ACTIVE",
            created_at=now - timedelta(days=13),
        )
        session.add(seg4)
        session.add(seg5)
        session.commit()

        # Adjustment on worklog 2 (quality deduction)
        adj1 = Adjustment(
            worklog_id=wl2.id,
            amount=-30.0,
            reason="Quality review deduction",
            status="ACTIVE",
            created_at=now - timedelta(days=12),
        )
        session.add(adj1)
        session.commit()

        # --- User 2: 2 worklogs ---

        wl3 = WorkLog(
            user_id=u2.id,
            title="Frontend Component Build",
            status="ACTIVE",
            created_at=now - timedelta(days=25),
        )
        session.add(wl3)
        session.commit()
        session.refresh(wl3)

        seg6 = TimeSegment(
            worklog_id=wl3.id,
            hours=8.0,
            rate=45.0,
            status="ACTIVE",
            created_at=now - timedelta(days=24),
        )
        seg7 = TimeSegment(
            worklog_id=wl3.id,
            hours=4.0,
            rate=45.0,
            status="ACTIVE",
            created_at=now - timedelta(days=23),
        )
        session.add(seg6)
        session.add(seg7)
        session.commit()

        # This worklog has an existing settled remittance (partially paid)
        wl4 = WorkLog(
            user_id=u2.id,
            title="Testing Automation Setup",
            status="CLOSED",
            created_at=now - timedelta(days=40),
        )
        session.add(wl4)
        session.commit()
        session.refresh(wl4)

        seg8 = TimeSegment(
            worklog_id=wl4.id,
            hours=5.0,
            rate=50.0,
            status="ACTIVE",
            created_at=now - timedelta(days=39),
        )
        session.add(seg8)
        session.commit()

        # Bonus adjustment
        adj2 = Adjustment(
            worklog_id=wl4.id,
            amount=25.0,
            reason="Early completion bonus",
            status="ACTIVE",
            created_at=now - timedelta(days=38),
        )
        session.add(adj2)
        session.commit()

        # Create a settled remittance for wl4 (already paid out)
        # wl4 total = (5 * 50) + 25 = 275
        rmtnc = Remittance(
            user_id=u2.id,
            amount=275.0,
            status="SETTLED",
            period=(now - timedelta(days=30)).strftime("%Y-%m"),
            created_at=now - timedelta(days=30),
        )
        session.add(rmtnc)
        session.commit()
        session.refresh(rmtnc)

        rw = RemittanceWorklog(
            remittance_id=rmtnc.id,
            worklog_id=wl4.id,
            amount=275.0,
        )
        session.add(rw)
        session.commit()

        logger.info("Seed data created successfully!")
        logger.info(f"  Worklog 1 (user1): API Integration - 4h+3h @ $50 = $350")
        logger.info(f"  Worklog 2 (user1): DB Migration - 6h+2h @ $55 - $30 adj = $410")
        logger.info(f"  Worklog 3 (user2): Frontend Build - 8h+4h @ $45 = $540")
        logger.info(f"  Worklog 4 (user2): Testing Setup - 5h @ $50 + $25 bonus = $275 (SETTLED)")


if __name__ == "__main__":
    seed()
