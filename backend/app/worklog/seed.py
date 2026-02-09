from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.db import engine
from app.worklog.models import Freelancer, TimeEntry, WorkLog


def seed_worklog_data():
    with Session(engine) as session:
        existing = session.exec(select(Freelancer)).first()
        if existing:
            print("Worklog data already seeded")
            return

        fl1 = Freelancer(
            name="John Doe", email="john@example.com", rate_per_hour=50.0
        )
        fl2 = Freelancer(
            name="Jane Smith", email="jane@example.com", rate_per_hour=75.0
        )
        fl3 = Freelancer(
            name="Bob Johnson", email="bob@example.com", rate_per_hour=60.0
        )
        session.add(fl1)
        session.add(fl2)
        session.add(fl3)
        session.commit()
        session.refresh(fl1)
        session.refresh(fl2)
        session.refresh(fl3)

        wl1 = WorkLog(
            freelancer_id=fl1.id,
            task_name="Build Authentication System",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        wl2 = WorkLog(
            freelancer_id=fl1.id,
            task_name="Implement Payment Gateway",
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        wl3 = WorkLog(
            freelancer_id=fl2.id,
            task_name="Design Dashboard UI",
            created_at=datetime.utcnow() - timedelta(days=8),
        )
        wl4 = WorkLog(
            freelancer_id=fl2.id,
            task_name="API Integration",
            created_at=datetime.utcnow() - timedelta(days=3),
        )
        wl5 = WorkLog(
            freelancer_id=fl3.id,
            task_name="Database Optimization",
            created_at=datetime.utcnow() - timedelta(days=7),
        )
        wl6 = WorkLog(
            freelancer_id=fl3.id,
            task_name="Write Unit Tests",
            created_at=datetime.utcnow() - timedelta(days=2),
        )

        session.add(wl1)
        session.add(wl2)
        session.add(wl3)
        session.add(wl4)
        session.add(wl5)
        session.add(wl6)
        session.commit()
        session.refresh(wl1)
        session.refresh(wl2)
        session.refresh(wl3)
        session.refresh(wl4)
        session.refresh(wl5)
        session.refresh(wl6)

        te1 = TimeEntry(
            worklog_id=wl1.id,
            description="Setup OAuth2 flow",
            hours=4.5,
            rate=50.0,
            amount=225.0,
            entry_date=datetime.utcnow() - timedelta(days=10),
        )
        te2 = TimeEntry(
            worklog_id=wl1.id,
            description="Implement JWT tokens",
            hours=3.0,
            rate=50.0,
            amount=150.0,
            entry_date=datetime.utcnow() - timedelta(days=9),
        )
        te3 = TimeEntry(
            worklog_id=wl1.id,
            description="Add password reset",
            hours=2.5,
            rate=50.0,
            amount=125.0,
            entry_date=datetime.utcnow() - timedelta(days=8),
        )

        te4 = TimeEntry(
            worklog_id=wl2.id,
            description="Stripe integration",
            hours=5.0,
            rate=50.0,
            amount=250.0,
            entry_date=datetime.utcnow() - timedelta(days=5),
        )
        te5 = TimeEntry(
            worklog_id=wl2.id,
            description="Payment webhooks",
            hours=3.5,
            rate=50.0,
            amount=175.0,
            entry_date=datetime.utcnow() - timedelta(days=4),
        )

        te6 = TimeEntry(
            worklog_id=wl3.id,
            description="Create wireframes",
            hours=6.0,
            rate=75.0,
            amount=450.0,
            entry_date=datetime.utcnow() - timedelta(days=8),
        )
        te7 = TimeEntry(
            worklog_id=wl3.id,
            description="Design components",
            hours=8.0,
            rate=75.0,
            amount=600.0,
            entry_date=datetime.utcnow() - timedelta(days=7),
        )

        te8 = TimeEntry(
            worklog_id=wl4.id,
            description="Connect REST APIs",
            hours=4.0,
            rate=75.0,
            amount=300.0,
            entry_date=datetime.utcnow() - timedelta(days=3),
        )

        te9 = TimeEntry(
            worklog_id=wl5.id,
            description="Add database indexes",
            hours=3.0,
            rate=60.0,
            amount=180.0,
            entry_date=datetime.utcnow() - timedelta(days=7),
        )
        te10 = TimeEntry(
            worklog_id=wl5.id,
            description="Query optimization",
            hours=4.5,
            rate=60.0,
            amount=270.0,
            entry_date=datetime.utcnow() - timedelta(days=6),
        )

        te11 = TimeEntry(
            worklog_id=wl6.id,
            description="Write API tests",
            hours=5.0,
            rate=60.0,
            amount=300.0,
            entry_date=datetime.utcnow() - timedelta(days=2),
        )

        session.add(te1)
        session.add(te2)
        session.add(te3)
        session.add(te4)
        session.add(te5)
        session.add(te6)
        session.add(te7)
        session.add(te8)
        session.add(te9)
        session.add(te10)
        session.add(te11)
        session.commit()

        for wl in [wl1, wl2, wl3, wl4, wl5, wl6]:
            entries = session.exec(
                select(TimeEntry).where(TimeEntry.worklog_id == wl.id)
            ).all()
            total = 0.0
            for e in entries:
                total += e.amount
            wl.total_amount = total
            session.add(wl)
        session.commit()

        print("Worklog data seeded successfully")


if __name__ == "__main__":
    seed_worklog_data()
