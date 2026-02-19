import logging
import random
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.db import engine
from app.core.security import get_password_hash
from app.models import TimeEntry, User, Worklog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FREELANCERS = [
    ("Alice Mercer", "alice@example.com", 75.0),
    ("Bob Huang", "bob@example.com", 65.0),
    ("Carol Jensen", "carol@example.com", 85.0),
    ("David Park", "david@example.com", 90.0),
    ("Elena Russo", "elena@example.com", 70.0),
    ("Frank Okafor", "frank@example.com", 80.0),
    ("Grace Nakamura", "grace@example.com", 95.0),
    ("Henry Diaz", "henry@example.com", 60.0),
    ("Iris Santos", "iris@example.com", 78.0),
    ("James Kowalski", "james@example.com", 88.0),
    ("Kayla Thompson", "kayla@example.com", 72.0),
    ("Leo Fernandez", "leo@example.com", 55.0),
    ("Maya Patel", "maya@example.com", 82.0),
    ("Nate Williams", "nate@example.com", 68.0),
    ("Olivia Chen", "olivia@example.com", 92.0),
]

WORKLOG_TITLES = [
    "API Gateway Integration",
    "User Authentication Redesign",
    "Payment Processing Module",
    "Database Query Optimization",
    "Mobile App UI Components",
    "CI/CD Pipeline Setup",
    "Report Generation Service",
    "Notification System",
    "Search Indexing Feature",
    "Analytics Dashboard",
    "Data Migration Scripts",
    "OAuth2 Provider Setup",
    "Cache Layer Implementation",
    "PDF Export Module",
    "Rate Limiting Middleware",
    "Admin Panel Development",
    "Audit Logging System",
    "Multi-Tenant Architecture",
    "Webhook Event Handler",
    "Email Template Engine",
    "File Upload Service",
    "Background Job Processor",
    "GraphQL Schema Design",
    "API Documentation Update",
    "Load Testing & Profiling",
    "Onboarding Flow UI",
    "SSO Integration",
    "Automated Test Coverage",
    "Billing Integration",
    "Security Audit Fixes",
]

ENTRY_DESCRIPTIONS = [
    "Implemented core logic and unit tests",
    "Reviewed requirements and drafted design doc",
    "Fixed edge cases found during QA",
    "Refactored existing code for clarity",
    "Wrote integration tests for happy path",
    "Debugged production issue and deployed hotfix",
    "Updated documentation and changelog",
    "Code review and addressed feedback",
    "Performance profiling and optimisation",
    "Setup local dev environment and tooling",
    "Pair programming session with backend team",
    "Database schema changes and migration",
    "Deployed to staging and ran smoke tests",
    "Synced with product on acceptance criteria",
    "Investigated third-party library compatibility",
]


def _already_seeded(session: Session) -> bool:
    return session.exec(
        select(User).where(User.email == "alice@example.com")
    ).first() is not None


def seed(session: Session) -> None:
    if _already_seeded(session):
        logger.info("Seed data already present, skipping.")
        return

    logger.info("Seeding freelancers, worklogs, and time entries…")

    freelancer_objs: list[User] = []
    for full_name, email, rate in FREELANCERS:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_superuser=False,
            hourly_rate=rate,
        )
        session.add(user)
        freelancer_objs.append(user)

    session.commit()
    for u in freelancer_objs:
        session.refresh(u)

    # Assign 2 worklogs per freelancer (30 total)
    worklog_pool = list(WORKLOG_TITLES)
    random.shuffle(worklog_pool)

    worklog_objs: list[Worklog] = []
    for i, freelancer in enumerate(freelancer_objs):
        for j in range(2):
            title = worklog_pool.pop()
            wl = Worklog(
                title=title,
                description=f"Ongoing work on {title.lower()} for the platform.",
                freelancer_id=freelancer.id,
                hourly_rate=freelancer.hourly_rate or 60.0,
                created_at=datetime.utcnow() - timedelta(days=random.randint(90, 180)),
                updated_at=datetime.utcnow(),
            )
            session.add(wl)
            worklog_objs.append(wl)

    session.commit()
    for wl in worklog_objs:
        session.refresh(wl)

    # Generate time entries over the past 6 months (~50 entries per worklog)
    base_date = datetime.utcnow()
    for wl in worklog_objs:
        days_back = 180
        for _ in range(50):
            # Pick a random day in the past 6 months, skip Sundays
            offset = random.randint(1, days_back)
            entry_day = base_date - timedelta(days=offset)
            if entry_day.weekday() == 6:  # Sunday
                entry_day -= timedelta(days=1)

            work_hours = round(random.uniform(1.0, 4.5), 2)
            start_hour = random.randint(8, 16)
            start_time = entry_day.replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            )
            end_time = start_time + timedelta(hours=work_hours)

            entry = TimeEntry(
                worklog_id=wl.id,
                start_time=start_time,
                end_time=end_time,
                hours=work_hours,
                description=random.choice(ENTRY_DESCRIPTIONS),
                created_at=start_time,
            )
            session.add(entry)

    session.commit()
    logger.info(
        "Seeded %d freelancers, %d worklogs, ~%d time entries.",
        len(freelancer_objs),
        len(worklog_objs),
        len(worklog_objs) * 50,
    )


def main() -> None:
    with Session(engine) as session:
        seed(session)


if __name__ == "__main__":
    main()
