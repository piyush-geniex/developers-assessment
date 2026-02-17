import logging
import random
from datetime import datetime, timedelta
from uuid import uuid4

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import Payment, PaymentBatch, Task, TimeEntry, User, WorkLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_seed_data(session: Session) -> None:
    """Create comprehensive seed data for tasks, worklogs, time entries, and payments."""
    users = session.exec(select(User)).all()
    if not users:
        logger.info("No users found, skipping seed data creation")
        return

    # Use existing users as freelancers, skip superuser if it's the first one
    freelancers = users[1:] if len(users) > 1 else users[:1]
    if not freelancers:
        logger.info("No freelancers found, skipping seed data creation")
        return

    logger.info(f"Creating seed data with {len(freelancers)} freelancer(s)")

    # Create diverse tasks
    task_data = [
        ("Frontend Development", "Build responsive React components with TypeScript"),
        ("Backend API", "Create RESTful API endpoints with FastAPI"),
        ("Database Design", "Design PostgreSQL schema and write migrations"),
        ("Testing", "Write unit and integration tests with pytest"),
        ("UI/UX Design", "Design user interface mockups and prototypes"),
        ("DevOps Setup", "Configure CI/CD pipelines and Docker containers"),
        ("Code Review", "Review pull requests and provide feedback"),
        ("Documentation", "Write technical documentation and API docs"),
        ("Bug Fixes", "Fix critical bugs in production system"),
        ("Performance Optimization", "Optimize database queries and API response times"),
        ("Security Audit", "Conduct security review and implement fixes"),
        ("Mobile App Development", "Build iOS and Android mobile applications"),
    ]

    tasks = []
    base_date = datetime.utcnow() - timedelta(days=60)

    for title, description in task_data:
        task_id = uuid4()
        existing = session.exec(select(Task).where(Task.title == title)).first()
        if not existing:
            task = Task(
                id=task_id,
                title=title,
                description=description,
                created_at=base_date + timedelta(days=random.randint(0, 30)),
            )
            session.add(task)
            session.commit()
            tasks.append(task)
        else:
            tasks.append(existing)

    logger.info(f"Created {len(tasks)} tasks")

    # Create worklogs with varied statuses and dates
    worklogs = []
    statuses = ["PENDING", "COMPLETED"]
    worklog_dates = []

    for i in range(20):  # Create 20 worklogs
        task = random.choice(tasks)
        freelancer = random.choice(freelancers)
        status = random.choice(statuses)
        # Distribute worklogs over the past 60 days
        days_ago = random.randint(0, 60)
        worklog_date = datetime.utcnow() - timedelta(days=days_ago)
        worklog_dates.append(worklog_date)

        existing = session.exec(
            select(WorkLog).where(WorkLog.task_id == task.id).where(
                WorkLog.freelancer_id == freelancer.id
            )
        ).first()

        if not existing:
            wl = WorkLog(
                id=uuid4(),
                task_id=task.id,
                freelancer_id=freelancer.id,
                status=status,
                created_at=worklog_date,
                updated_at=worklog_date,
            )
            session.add(wl)
            session.commit()
            worklogs.append(wl)
        else:
            worklogs.append(existing)

    logger.info(f"Created {len(worklogs)} worklogs")

    # Create time entries with varied hours and rates
    time_entry_descriptions = [
        "Implemented core functionality",
        "Fixed critical bugs",
        "Code review and refactoring",
        "Writing unit tests",
        "Database query optimization",
        "API endpoint development",
        "Frontend component implementation",
        "Documentation updates",
        "Performance testing",
        "Security improvements",
        "Integration with third-party services",
        "UI/UX improvements",
    ]

    for wl in worklogs:
        # Create 1-5 time entries per worklog
        num_entries = random.randint(1, 5)
        base_rate = random.uniform(40.0, 100.0)  # Rates between $40-$100/hr

        for j in range(num_entries):
            hours = round(random.uniform(1.0, 8.0), 2)  # 1-8 hours
            rate = round(base_rate + random.uniform(-10.0, 10.0), 2)
            description = random.choice(time_entry_descriptions)

            # Entry date should be within worklog date range
            entry_date = wl.created_at + timedelta(
                days=random.randint(0, 7), hours=random.randint(0, 23)
            )

            existing = session.exec(
                select(TimeEntry).where(
                    TimeEntry.worklog_id == wl.id
                ).where(TimeEntry.entry_date == entry_date)
            ).first()

            if not existing:
                te = TimeEntry(
                    id=uuid4(),
                    worklog_id=wl.id,
                    hours=hours,
                    rate=rate,
                    description=description,
                    entry_date=entry_date,
                )
                session.add(te)
                session.commit()

    logger.info("Created time entries")

    # Create payment batches
    completed_worklogs = [wl for wl in worklogs if wl.status == "COMPLETED"]
    if completed_worklogs:
        # Create 2-3 payment batches
        num_batches = min(3, len(completed_worklogs) // 5)

        for batch_num in range(num_batches):
            # Payment batch covering last 30 days
            end_date = datetime.utcnow() - timedelta(days=batch_num * 10)
            start_date = end_date - timedelta(days=30)

            batch = PaymentBatch(
                id=uuid4(),
                start_date=start_date,
                end_date=end_date,
                status="COMPLETED" if batch_num < 2 else "PENDING",
                notes=f"Payment batch for period {start_date.date()} to {end_date.date()}",
                created_at=end_date,
                processed_at=end_date if batch_num < 2 else None,
                total_amount=0.0,
            )
            session.add(batch)
            session.commit()

            # Create payments for completed worklogs in this period
            batch_worklogs = [
                wl
                for wl in completed_worklogs
                if start_date <= wl.created_at <= end_date
            ][:10]  # Limit to 10 worklogs per batch

            batch_total = 0.0
            for wl in batch_worklogs:
                # Calculate total earnings from time entries
                time_entries = session.exec(
                    select(TimeEntry).where(TimeEntry.worklog_id == wl.id)
                ).all()

                if time_entries:
                    total_earnings = sum(te.hours * te.rate for te in time_entries)
                    batch_total += total_earnings

                    payment = Payment(
                        id=uuid4(),
                        worklog_id=wl.id,
                        payment_batch_id=batch.id,
                        amount=round(total_earnings, 2),
                        status="COMPLETED" if batch_num < 2 else "PENDING",
                        created_at=end_date,
                        processed_at=end_date if batch_num < 2 else None,
                    )
                    session.add(payment)
                    session.commit()

            # Update batch total
            batch.total_amount = round(batch_total, 2)
            session.add(batch)
            session.commit()

            logger.info(
                f"Created payment batch {batch_num + 1} with {len(batch_worklogs)} payments, total: ${batch_total:.2f}"
            )

    logger.info("Seed data creation completed")


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
