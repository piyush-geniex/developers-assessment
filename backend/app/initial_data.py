import logging
from datetime import datetime, timedelta
from uuid import uuid4

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import Task, TimeEntry, User, WorkLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_seed_data(session: Session) -> None:
    """Create seed data for tasks, worklogs, and time entries."""
    users = session.exec(select(User)).all()
    if not users:
        logger.info("No users found, skipping seed data creation")
        return

    freelancer = users[0]
    if len(users) > 1:
        freelancer = users[1]

    tasks = [
        Task(id=uuid4(), title="Frontend Development", description="Build React components"),
        Task(id=uuid4(), title="Backend API", description="Create REST endpoints"),
        Task(id=uuid4(), title="Database Design", description="Design schema and migrations"),
        Task(id=uuid4(), title="Testing", description="Write unit and integration tests"),
    ]

    for task in tasks:
        existing = session.get(Task, task.id)
        if not existing:
            session.add(task)
            session.commit()

    worklogs = []
    base_date = datetime.utcnow() - timedelta(days=30)

    for i, task in enumerate(tasks):
        wl = WorkLog(
            id=uuid4(),
            task_id=task.id,
            freelancer_id=freelancer.id,
            status="PENDING",
            created_at=base_date + timedelta(days=i * 5),
            updated_at=base_date + timedelta(days=i * 5),
        )
        existing = session.exec(
            select(WorkLog).where(WorkLog.task_id == task.id)
        ).first()
        if not existing:
            session.add(wl)
            session.commit()
            worklogs.append(wl)
        else:
            worklogs.append(existing)

    for i, wl in enumerate(worklogs):
        for j in range(3):
            te = TimeEntry(
                id=uuid4(),
                worklog_id=wl.id,
                hours=2.5 + (j * 0.5),
                rate=50.0 + (i * 5),
                description=f"Time entry {j+1} for {tasks[i].title}",
                entry_date=wl.created_at + timedelta(hours=j * 2),
            )
            existing = session.exec(
                select(TimeEntry).where(
                    TimeEntry.worklog_id == wl.id,
                    TimeEntry.entry_date == te.entry_date,
                )
            ).first()
            if not existing:
                session.add(te)
                session.commit()


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        create_seed_data(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
