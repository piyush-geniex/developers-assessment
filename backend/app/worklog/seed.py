import logging
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.worklog.models import Freelancer, Payment, WorkLog

logger = logging.getLogger(__name__)


def seed_worklog_data(session: Session) -> None:
    """Seed freelancers, worklogs, and time entries for development."""

    # Check if data already exists
    existing = session.exec(select(Freelancer)).first()
    if existing:
        logger.info("Worklog seed data already exists, skipping")
        return

    logger.info("Seeding worklog data...")

    # Create freelancers
    frs = [
        Freelancer(name="Alice Johnson", email="alice@example.com", hourly_rate=75.0),
        Freelancer(name="Bob Smith", email="bob@example.com", hourly_rate=60.0),
        Freelancer(name="Carol Davis", email="carol@example.com", hourly_rate=90.0),
        Freelancer(name="Dan Wilson", email="dan@example.com", hourly_rate=55.0),
        Freelancer(name="Eve Martinez", email="eve@example.com", hourly_rate=80.0),
    ]
    for f in frs:
        session.add(f)
    session.commit()

    # Refresh to get IDs
    for f in frs:
        session.refresh(f)

    now = datetime.utcnow()

    # Create worklogs with time entries
    wl_data = [
        {
            "fr": frs[0],
            "task": "Build REST API endpoints",
            "desc": "Implement CRUD endpoints for user management",
            "days_ago": 5,
            "entries": [
                {"hrs": 3.0, "offset_hrs": 0},
                {"hrs": 4.5, "offset_hrs": 4},
                {"hrs": 2.0, "offset_hrs": 24},
            ],
        },
        {
            "fr": frs[0],
            "task": "Database schema design",
            "desc": "Design and implement PostgreSQL schema for the project",
            "days_ago": 12,
            "entries": [
                {"hrs": 5.0, "offset_hrs": 0},
                {"hrs": 3.0, "offset_hrs": 6},
            ],
        },
        {
            "fr": frs[1],
            "task": "Frontend dashboard layout",
            "desc": "Create responsive dashboard layout with sidebar navigation",
            "days_ago": 3,
            "entries": [
                {"hrs": 6.0, "offset_hrs": 0},
                {"hrs": 4.0, "offset_hrs": 8},
                {"hrs": 3.5, "offset_hrs": 24},
            ],
        },
        {
            "fr": frs[1],
            "task": "Authentication flow",
            "desc": "Implement login, signup, and password reset flows",
            "days_ago": 8,
            "entries": [
                {"hrs": 4.0, "offset_hrs": 0},
                {"hrs": 5.0, "offset_hrs": 5},
            ],
        },
        {
            "fr": frs[2],
            "task": "Payment integration",
            "desc": "Integrate Stripe payment processing for subscriptions",
            "days_ago": 2,
            "entries": [
                {"hrs": 7.0, "offset_hrs": 0},
                {"hrs": 5.5, "offset_hrs": 8},
                {"hrs": 4.0, "offset_hrs": 24},
                {"hrs": 3.0, "offset_hrs": 32},
            ],
        },
        {
            "fr": frs[2],
            "task": "Email notification system",
            "desc": "Build email templates and notification triggers",
            "days_ago": 15,
            "entries": [
                {"hrs": 3.5, "offset_hrs": 0},
                {"hrs": 2.5, "offset_hrs": 4},
            ],
        },
        {
            "fr": frs[3],
            "task": "Unit test coverage",
            "desc": "Write unit tests for core business logic modules",
            "days_ago": 4,
            "entries": [
                {"hrs": 4.0, "offset_hrs": 0},
                {"hrs": 3.0, "offset_hrs": 5},
                {"hrs": 2.5, "offset_hrs": 24},
            ],
        },
        {
            "fr": frs[3],
            "task": "CI/CD pipeline setup",
            "desc": "Configure GitHub Actions for automated testing and deployment",
            "days_ago": 10,
            "entries": [
                {"hrs": 5.0, "offset_hrs": 0},
                {"hrs": 4.0, "offset_hrs": 6},
            ],
        },
        {
            "fr": frs[4],
            "task": "Data migration scripts",
            "desc": "Write migration scripts for legacy data import",
            "days_ago": 6,
            "entries": [
                {"hrs": 6.0, "offset_hrs": 0},
                {"hrs": 4.5, "offset_hrs": 8},
                {"hrs": 3.0, "offset_hrs": 24},
            ],
        },
        {
            "fr": frs[4],
            "task": "API documentation",
            "desc": "Create OpenAPI documentation and usage examples",
            "days_ago": 1,
            "entries": [
                {"hrs": 3.0, "offset_hrs": 0},
                {"hrs": 2.0, "offset_hrs": 4},
            ],
        },
        {
            "fr": frs[0],
            "task": "Code review and refactoring",
            "desc": "Review PR submissions and refactor critical paths",
            "days_ago": 7,
            "entries": [
                {"hrs": 2.5, "offset_hrs": 0},
                {"hrs": 3.0, "offset_hrs": 3},
            ],
        },
        {
            "fr": frs[1],
            "task": "Performance optimization",
            "desc": "Profile and optimize slow database queries",
            "days_ago": 14,
            "entries": [
                {"hrs": 4.0, "offset_hrs": 0},
                {"hrs": 5.5, "offset_hrs": 5},
                {"hrs": 3.0, "offset_hrs": 24},
            ],
        },
        {
            "fr": frs[2],
            "task": "Security audit fixes",
            "desc": "Address findings from the security audit report",
            "days_ago": 9,
            "entries": [
                {"hrs": 6.0, "offset_hrs": 0},
                {"hrs": 4.0, "offset_hrs": 8},
            ],
        },
        {
            "fr": frs[3],
            "task": "Docker containerization",
            "desc": "Containerize all services with multi-stage Docker builds",
            "days_ago": 11,
            "entries": [
                {"hrs": 3.0, "offset_hrs": 0},
                {"hrs": 4.5, "offset_hrs": 4},
                {"hrs": 2.0, "offset_hrs": 24},
            ],
        },
        {
            "fr": frs[4],
            "task": "Monitoring and alerting",
            "desc": "Set up Prometheus metrics and Grafana dashboards",
            "days_ago": 13,
            "entries": [
                {"hrs": 5.0, "offset_hrs": 0},
                {"hrs": 3.5, "offset_hrs": 6},
                {"hrs": 4.0, "offset_hrs": 24},
            ],
        },
    ]

    for wl_d in wl_data:
        created = now - timedelta(days=wl_d["days_ago"])

        wl = WorkLog(
            type="worklog",
            freelancer_id=wl_d["fr"].id,
            task_name=wl_d["task"],
            description=wl_d["desc"],
            status="pending",
            created_at=created,
        )
        session.add(wl)
        session.commit()
        session.refresh(wl)

        for te_d in wl_d["entries"]:
            st = created + timedelta(hours=te_d["offset_hrs"])
            et = st + timedelta(hours=te_d["hrs"])

            te = WorkLog(
                type="time_entry",
                parent_id=wl.id,
                start_time=st,
                end_time=et,
                hours=te_d["hrs"],
                created_at=st,
            )
            session.add(te)
            session.commit()

    logger.info("Worklog seed data created successfully")
