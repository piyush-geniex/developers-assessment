import logging
from datetime import date, timedelta

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import Item, TimeEntry, User, WorkLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_worklogs(session: Session) -> None:
    """Seed worklogs and time entries for development. Spread across 90 days for date-range showcase."""
    from app.core.security import get_password_hash
    from app.crud import get_user_by_email

    cnt = session.exec(select(WorkLog)).first()
    if cnt:
        return

    admin = get_user_by_email(session=session, email="admin@example.com")
    if not admin:
        return

    # Create freelancers
    freelancers_data = [
        ("freelancer@example.com", "Jane Freelancer", 50.0),
        ("alex.dev@example.com", "Alex Developer", 75.0),
        ("sarah.design@example.com", "Sarah Designer", 60.0),
    ]
    freelancers = []
    for email, name, rate in freelancers_data:
        usr = get_user_by_email(session=session, email=email)
        if not usr:
            usr = User(
                email=email,
                hashed_password=get_password_hash("changethis"),
                is_active=True,
                is_superuser=False,
                full_name=name,
            )
            session.add(usr)
        freelancers.append((usr, rate))
    session.commit()

    # Get or create items (tasks)
    items_data = [
        ("API Integration", "Integrate payment API"),
        ("Dashboard UI", "Build admin dashboard"),
        ("Auth System", "Implement JWT authentication"),
        ("Report Export", "Add CSV/PDF export"),
        ("Mobile Responsiveness", "Fix responsive layout"),
    ]
    items = list(session.exec(select(Item).limit(10)).all())
    if len(items) < len(items_data):
        for title, desc in items_data:
            it = Item(title=title, description=desc, owner_id=admin.id)
            session.add(it)
        session.commit()
        items = list(session.exec(select(Item).limit(10)).all())

    # Worklogs spread across ~90 days: some in past month, some in past 2 weeks, various freelancers
    today = date.today()
    # Entries spanning: 90 days ago -> today
    worklog_configs = [
        (0, 0, -85, -82),   # Jane, item 0, entries ~85-82 days ago
        (0, 1, -70, -65),   # Jane, item 1, entries ~70-65 days ago
        (1, 2, -45, -42),   # Alex, item 2, entries ~45-42 days ago
        (1, 0, -30, -28),   # Alex, item 0, entries ~30-28 days ago
        (2, 3, -21, -18),   # Sarah, item 3, entries ~21-18 days ago
        (0, 4, -14, -10),   # Jane, item 4, entries ~14-10 days ago
        (1, 1, -7, -5),     # Alex, item 1, entries ~7-5 days ago
        (2, 0, -3, -1),     # Sarah, item 0, entries ~3-1 days ago
        (0, 2, -2, 0),      # Jane, item 2, entries last 2 days (recent)
    ]

    for fl_idx, item_idx, start_off, end_off in worklog_configs:
        fl, base_rate = freelancers[fl_idx % len(freelancers)]
        it = items[item_idx % len(items)]
        start_d = today + timedelta(days=start_off)
        end_d = today + timedelta(days=end_off)
        num_days = max(1, (end_d - start_d).days + 1)

        wl = WorkLog(
            item_id=it.id,
            user_id=fl.id,
            status="pending",
        )
        session.add(wl)
        session.commit()
        session.refresh(wl)

        for j in range(min(num_days, 5)):
            entry_d = start_d + timedelta(days=j)
            te = TimeEntry(
                worklog_id=wl.id,
                hours=round(2.0 + (j % 3) * 0.5, 1),
                rate=base_rate + (item_idx * 5),
                entry_date=entry_d,
                description=f"Work on {it.title}",
            )
            session.add(te)
        session.commit()

    logger.info("Worklog seed data created")


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        seed_worklogs(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
