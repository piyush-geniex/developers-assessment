"""
Seed script to populate the database with realistic worklog data.

Run with: python -m scripts.seed_worklogs

Creates:
- 5 Freelancers with varied hourly rates
- 50+ WorkLogs with mixed statuses
- Multiple TimeEntries per WorkLog
- 2 existing PaymentBatches for history
"""
import logging
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlmodel import Session, select

from app.core.db import engine
from app.core.security import get_password_hash
from app.models import (
    Freelancer,
    PaymentBatch,
    PaymentBatchStatus,
    TimeEntry,
    User,
    WorkLog,
    WorkLogStatus,
)

# Default password for seeded freelancers
DEFAULT_FREELANCER_PASSWORD = "user1234"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Freelancer data
FREELANCERS = [
    {"name": "Alex Chen", "email": "alex.chen@example.com", "hourly_rate": Decimal("75.00")},
    {"name": "Sarah Johnson", "email": "sarah.j@example.com", "hourly_rate": Decimal("95.00")},
    {"name": "Miguel Rodriguez", "email": "miguel.r@example.com", "hourly_rate": Decimal("65.00")},
    {"name": "Emma Williams", "email": "emma.w@example.com", "hourly_rate": Decimal("110.00")},
    {"name": "James Kim", "email": "james.kim@example.com", "hourly_rate": Decimal("85.00")},
]

# Task descriptions for realistic worklogs
TASK_DESCRIPTIONS = [
    "Implement user authentication flow",
    "Design and build REST API endpoints",
    "Create responsive dashboard UI",
    "Fix critical performance issues",
    "Refactor legacy database queries",
    "Set up CI/CD pipeline",
    "Write unit tests for payment module",
    "Integrate third-party analytics",
    "Optimize image loading performance",
    "Build notification system",
    "Create admin management panel",
    "Implement search functionality",
    "Design database schema for reporting",
    "Build export to CSV feature",
    "Fix mobile responsiveness issues",
    "Implement rate limiting",
    "Create user onboarding flow",
    "Build real-time chat feature",
    "Optimize API response times",
    "Implement caching layer",
    "Create data visualization charts",
    "Build file upload system",
    "Implement email notification templates",
    "Fix cross-browser compatibility",
    "Create automated backup system",
    "Build user permissions system",
    "Implement audit logging",
    "Create API documentation",
    "Build webhook integration",
    "Implement two-factor authentication",
]


def random_date(start_days_ago: int, end_days_ago: int) -> datetime:
    """Generate a random datetime within a range of days ago."""
    days_ago = random.randint(end_days_ago, start_days_ago)
    hours = random.randint(8, 18)  # Working hours
    minutes = random.randint(0, 59)
    return datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 12)) + timedelta(hours=hours, minutes=minutes)


def create_time_entries(session: Session, worklog: WorkLog, base_date: datetime) -> list[TimeEntry]:
    """Create realistic time entries for a worklog."""
    entries = []
    num_entries = random.randint(2, 8)

    current_date = base_date

    for i in range(num_entries):
        # Random start time during working hours
        start_hour = random.randint(9, 16)
        start_minute = random.choice([0, 15, 30, 45])
        start_time = current_date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)

        # Duration between 30 mins and 4 hours
        duration_minutes = random.choice([30, 45, 60, 90, 120, 150, 180, 240])
        end_time = start_time + timedelta(minutes=duration_minutes)

        notes_options = [
            None,
            "Initial implementation",
            "Bug fixes and refinements",
            "Code review feedback",
            "Testing and documentation",
            "Meeting with team",
            "Research and planning",
        ]

        entry = TimeEntry(
            work_log_id=worklog.id,
            start_time=start_time,
            end_time=end_time,
            notes=random.choice(notes_options),
        )
        entries.append(entry)
        session.add(entry)

        # Move to next day for next entry (spread across days)
        if random.random() > 0.5:
            current_date = current_date + timedelta(days=1)

    return entries


def seed_data():
    """Main seeding function."""
    with Session(engine) as session:
        # Check if data already exists
        existing_freelancers = session.exec(select(Freelancer)).first()
        if existing_freelancers:
            logger.info("Seed data already exists. Skipping...")
            return

        logger.info("Starting database seeding...")

        # Get a superuser for payment batches
        superuser = session.exec(select(User).where(User.is_superuser == True)).first()
        if not superuser:
            logger.error("No superuser found. Please run initial_data.py first.")
            return

        # Create freelancers with default password
        freelancers = []
        hashed_password = get_password_hash(DEFAULT_FREELANCER_PASSWORD)
        for f_data in FREELANCERS:
            freelancer = Freelancer(**f_data, hashed_password=hashed_password)
            session.add(freelancer)
            freelancers.append(freelancer)
            logger.info(f"Created freelancer: {freelancer.name} (password: {DEFAULT_FREELANCER_PASSWORD})")

        session.flush()

        # Create worklogs with different statuses
        worklogs = []
        used_tasks = set()

        # Distribution: 30 PENDING, 12 APPROVED, 6 REJECTED, 12 PAID
        status_distribution = (
            [WorkLogStatus.PENDING] * 30 +
            [WorkLogStatus.APPROVED] * 12 +
            [WorkLogStatus.REJECTED] * 6 +
            [WorkLogStatus.PAID] * 12
        )
        random.shuffle(status_distribution)

        for i, status in enumerate(status_distribution):
            freelancer = random.choice(freelancers)

            # Pick a task (allow some repeats for different freelancers)
            task = random.choice(TASK_DESCRIPTIONS)

            # Dates spread over last 60 days
            created_at = random_date(60, 1)

            worklog = WorkLog(
                freelancer_id=freelancer.id,
                task_description=task,
                status=status,
                created_at=created_at,
                updated_at=created_at + timedelta(days=random.randint(0, 5)),
            )
            session.add(worklog)
            worklogs.append(worklog)

        session.flush()
        logger.info(f"Created {len(worklogs)} worklogs")

        # Create time entries for each worklog
        for worklog in worklogs:
            create_time_entries(session, worklog, worklog.created_at)

        session.flush()
        logger.info("Created time entries for all worklogs")

        # Create 2 payment batches for paid worklogs
        paid_worklogs = [w for w in worklogs if w.status == WorkLogStatus.PAID]

        if paid_worklogs:
            # Split paid worklogs into 2 batches
            mid = len(paid_worklogs) // 2
            batch1_worklogs = paid_worklogs[:mid]
            batch2_worklogs = paid_worklogs[mid:]

            # Calculate totals and create batches
            for batch_idx, batch_worklogs in enumerate([batch1_worklogs, batch2_worklogs], 1):
                if not batch_worklogs:
                    continue

                # Calculate total amount
                total_amount = Decimal("0.00")
                for wl in batch_worklogs:
                    freelancer = session.get(Freelancer, wl.freelancer_id)
                    # Get time entries for this worklog
                    entries = session.exec(
                        select(TimeEntry).where(TimeEntry.work_log_id == wl.id)
                    ).all()
                    total_minutes = sum(
                        (e.end_time - e.start_time).total_seconds() / 60
                        for e in entries
                    )
                    total_amount += (Decimal(total_minutes) / Decimal(60)) * freelancer.hourly_rate

                batch = PaymentBatch(
                    processed_by_id=superuser.id,
                    total_amount=total_amount.quantize(Decimal("0.01")),
                    status=PaymentBatchStatus.COMPLETED,
                    processed_at=datetime.utcnow() - timedelta(days=30 - batch_idx * 15),
                    notes=f"Payment cycle {batch_idx} - October 2024",
                )
                session.add(batch)
                session.flush()

                # Link worklogs to batch
                for wl in batch_worklogs:
                    wl.payment_batch_id = batch.id
                    session.add(wl)

                logger.info(f"Created payment batch {batch_idx} with {len(batch_worklogs)} worklogs, total: ${total_amount}")

        session.commit()
        logger.info("Database seeding completed successfully!")

        # Print summary
        logger.info("\n=== SEED DATA SUMMARY ===")
        logger.info(f"Freelancers: {len(freelancers)}")
        logger.info(f"Freelancer default password: {DEFAULT_FREELANCER_PASSWORD}")
        logger.info(f"Total WorkLogs: {len(worklogs)}")
        logger.info(f"  - PENDING: {sum(1 for w in worklogs if w.status == WorkLogStatus.PENDING)}")
        logger.info(f"  - APPROVED: {sum(1 for w in worklogs if w.status == WorkLogStatus.APPROVED)}")
        logger.info(f"  - REJECTED: {sum(1 for w in worklogs if w.status == WorkLogStatus.REJECTED)}")
        logger.info(f"  - PAID: {sum(1 for w in worklogs if w.status == WorkLogStatus.PAID)}")
        logger.info("========================\n")


def main():
    seed_data()


if __name__ == "__main__":
    main()
