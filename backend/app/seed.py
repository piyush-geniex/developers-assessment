from datetime import datetime, timedelta
from uuid import uuid4

from sqlmodel import Session, select

from app import crud
from app.models import ItemCreate, Task, TimeEntry, User, UserCreate, UserRole

SEED_PASSWORD = "password123"

FIRST_NAMES = [
    "Jordan", "Sam", "Morgan", "Casey", "Riley", "Alex", "Taylor", "Jamie", "Quinn", "Dakota",
    "Avery", "Cameron", "Sage", "River", "Kai", "Phoenix", "Rowan", "Skylar", "Finley", "Reese",
    "Emerson", "Blake", "Parker", "Hayden", "Drew",
]

LAST_NAMES = [
    "Lee", "Chen", "Taylor", "Rivera", "Nguyen", "Martinez", "Anderson", "Kim", "Patel", "Johnson",
    "Garcia", "Williams", "Brown", "Davis", "Miller", "Wilson", "Moore", "Jackson", "Martin", "Thompson",
    "White", "Lopez", "Gonzalez", "Harris", "Clark",
]

HOURLY_RATES = [65.0, 72.0, 78.0, 85.0, 92.0, 95.0, 105.0, 68.0, 88.0, 98.0]

TASK_PREFIXES = [
    "User authentication", "Payment processing", "Time tracking", "Invoice generation", "Email notifications",
    "Dashboard analytics", "Data import/export", "Rate management", "API integration", "Mobile interface",
    "Admin panel", "Reporting system", "Search functionality", "File upload", "User permissions",
    "Session management", "Cache optimization", "Database migration", "Security audit", "Performance testing",
    "Code refactoring", "UI redesign", "Webhook handling", "Third-party sync", "Backup automation",
    "Monitoring setup", "Documentation", "Testing framework", "CI/CD pipeline", "Error tracking",
    "Feature flags", "A/B testing", "Localization", "Accessibility", "Dark mode",
    "Notification center", "Activity feed", "User profiles", "Settings panel", "Onboarding flow",
    "Password recovery", "Two-factor auth", "API rate limiting", "Data validation", "Batch processing",
    "Real-time updates", "PDF generation", "Chart rendering", "Calendar integration", "Chat system",
]

TASK_SUFFIXES = [
    "and session handling", "flow improvements", "workflow automation", "system redesign", "service integration",
    "feature implementation", "bug fixes", "performance optimization", "security hardening", "UI enhancement",
]

TIME_DESCRIPTIONS = [
    "Kickoff and requirements", "Implementation", "Code review", "Documentation", "Bug fixes", "Refactoring",
    "Design collaboration", "Integration testing", "Performance tuning", "Final review", "Research spike",
    "Backend work", "Frontend work", "E2E testing", "Database queries", "API endpoints", "UI components",
    "Unit tests", "Deployment prep", "Security review", "Client feedback", "Tech debt", "Optimization",
]

SEED_DAYS = 420
WORKDAY_START_HOUR = 9
SUNDAY_WEEKDAY = 6


def _day_start_utc(days_ago: int, hour: int = WORKDAY_START_HOUR, minute: int = 0) -> datetime:
    midnight_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    that_day = midnight_today - timedelta(days=days_ago)
    return that_day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def seed_db(session: Session) -> None:
    anchor_email = f"{FIRST_NAMES[0].lower()}.{LAST_NAMES[0].lower()}@example.com"
    if session.exec(select(User).where(User.email == anchor_email)).first():
        return

    seed_users = []
    for i in range(25):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[i % len(LAST_NAMES)]
        email = f"{first.lower()}.{last.lower()}{i if i >= len(FIRST_NAMES) else ''}@example.com"
        full_name = f"{first} {last}"
        rate = HOURLY_RATES[i % len(HOURLY_RATES)]
        
        user = crud.create_user(
            session=session,
            user_create=UserCreate(
                email=email,
                password=SEED_PASSWORD,
                full_name=full_name,
                role=UserRole.FREELANCER,
                hourly_rate=rate,
            ),
        )
        seed_users.append(user)

    seed_tasks = []
    for i in range(50):
        prefix = TASK_PREFIXES[i % len(TASK_PREFIXES)]
        suffix = TASK_SUFFIXES[i % len(TASK_SUFFIXES)]
        title = f"{prefix} {suffix}"
        description = f"Implement and deliver {prefix.lower()}"
        task = Task(id=uuid4(), title=title, description=description)
        session.add(task)
        seed_tasks.append(task)
    session.commit()
    for task in seed_tasks:
        session.refresh(task)

    time_entries = []
    for days_ago in range(SEED_DAYS):
        if days_ago % 7 == SUNDAY_WEEKDAY:
            continue
        
        for task_index, task in enumerate(seed_tasks):
            if (days_ago * 7 + task_index) % 3 == 0:
                continue
            
            user = seed_users[(task_index * 3 + days_ago) % len(seed_users)]
            start = _day_start_utc(days_ago, WORKDAY_START_HOUR, 0)
            hours = ((task_index + days_ago) % 6) + 1
            if hours > 4:
                hours = 3
            end = start + timedelta(hours=hours, minutes=((task_index + days_ago) % 4) * 15)
            entry_description = TIME_DESCRIPTIONS[(task_index * 2 + days_ago) % len(TIME_DESCRIPTIONS)]
            
            time_entries.append(
                TimeEntry(
                    task_id=task.id,
                    freelancer_id=user.id,
                    start_time=start,
                    end_time=end,
                    description=entry_description,
                )
            )
    
    session.add_all(time_entries)
    session.commit()

    for i, user in enumerate(seed_users[:10]):
        item_count = (i % 3) + 1
        for j in range(item_count):
            title = f"Document {i}-{j}"
            description = f"Internal resource for {user.full_name}"
            crud.create_item(session=session, item_in=ItemCreate(title=title, description=description), owner_id=user.id)
