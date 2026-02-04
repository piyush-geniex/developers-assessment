import logging
import uuid
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.core.db import engine
from app.models import User, WorkLog, TimeEntry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_worklogs(session: Session) -> None:
    """Seed sample worklog data for testing"""

    # Check if worklogs already exist
    existing = session.exec(select(WorkLog)).first()
    if existing:
        logger.info("Worklogs already exist, skipping seed")
        return

    # Get first user as freelancer
    users = session.exec(select(User)).all()
    if not users:
        logger.warning("No users found, cannot seed worklogs")
        return

    freelancer = users[0]
    logger.info(f"Using user {freelancer.email} as freelancer")

    # Create sample worklogs
    worklogs_data = [
        {
            "task_name": "Frontend Development - User Dashboard",
            "hourly_rate": 75.0,
            "time_entries": [
                {"date": date.today() - timedelta(days=5), "hours": 4.5, "description": "Implemented user profile component"},
                {"date": date.today() - timedelta(days=4), "hours": 6.0, "description": "Added authentication flow"},
                {"date": date.today() - timedelta(days=3), "hours": 5.5, "description": "Bug fixes and code review"},
            ]
        },
        {
            "task_name": "Backend API Development",
            "hourly_rate": 85.0,
            "time_entries": [
                {"date": date.today() - timedelta(days=7), "hours": 8.0, "description": "Created REST API endpoints"},
                {"date": date.today() - timedelta(days=6), "hours": 7.5, "description": "Database schema design and migration"},
                {"date": date.today() - timedelta(days=5), "hours": 4.0, "description": "Integration testing"},
            ]
        },
        {
            "task_name": "Mobile App Development",
            "hourly_rate": 90.0,
            "time_entries": [
                {"date": date.today() - timedelta(days=10), "hours": 6.5, "description": "React Native setup"},
                {"date": date.today() - timedelta(days=9), "hours": 8.0, "description": "Implemented navigation"},
                {"date": date.today() - timedelta(days=8), "hours": 5.0, "description": "API integration"},
            ]
        },
        {
            "task_name": "Database Optimization",
            "hourly_rate": 95.0,
            "time_entries": [
                {"date": date.today() - timedelta(days=2), "hours": 3.5, "description": "Query optimization"},
                {"date": date.today() - timedelta(days=1), "hours": 4.0, "description": "Index creation and testing"},
            ]
        },
    ]

    for wl_data in worklogs_data:
        # Calculate totals
        total_hours = sum(te["hours"] for te in wl_data["time_entries"])
        total_amount = total_hours * wl_data["hourly_rate"]

        # Create worklog
        worklog = WorkLog(
            task_name=wl_data["task_name"],
            freelancer_id=freelancer.id,
            hourly_rate=wl_data["hourly_rate"],
            total_hours=total_hours,
            total_amount=total_amount,
            status="PENDING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(worklog)
        session.commit()
        session.refresh(worklog)

        # Create time entries
        for te_data in wl_data["time_entries"]:
            time_entry = TimeEntry(
                worklog_id=worklog.id,
                description=te_data["description"],
                hours=te_data["hours"],
                date=te_data["date"],
                created_at=datetime.utcnow(),
            )
            session.add(time_entry)
            session.commit()

        logger.info(f"Created worklog: {worklog.task_name} (${total_amount:.2f})")

    logger.info("Worklog seeding completed successfully")


def main() -> None:
    logger.info("Seeding worklog data")
    with Session(engine) as session:
        seed_worklogs(session)


if __name__ == "__main__":
    main()
