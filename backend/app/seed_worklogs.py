import logging
import uuid
from datetime import date, timedelta
from sqlmodel import Session, select, delete
from app.core.db import engine
from app.models import User, WorkLog, TimeEntry, WorkLogStatus, UserCreate
from app.core.security import get_password_hash
from app import crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_worklogs():
    with Session(engine) as session:
        # 1. Clear existing worklogs to start fresh with new users
        logger.info("Cleaning up existing worklogs and entries...")
        session.exec(delete(TimeEntry))
        session.exec(delete(WorkLog))
        session.commit()

        # 2. Create 5 different freelancers
        freelancers = [
            ("Alice Johnson", "alice@example.com"),
            ("Bob Smith", "bob@example.com"),
            ("Charlie Davis", "charlie@example.com"),
            ("Diana Prince", "diana@example.com"),
            ("Edward Norton", "edward@example.com"),
        ]
        
        db_freelancers = []
        for name, email in freelancers:
            user = session.exec(select(User).where(User.email == email)).first()
            if not user:
                logger.info(f"Creating user: {name}")
                user_in = UserCreate(
                    email=email,
                    password="changethis",
                    full_name=name,
                    is_superuser=False,
                )
                user = crud.create_user(session=session, user_create=user_in)
            db_freelancers.append(user)

        logger.info(f"Seeding worklogs for {len(db_freelancers)} freelancers")

        # 3. Create worklogs distributed among freelancers
        tasks = [
            ("Fix landing page alignment", 5, 50.0),
            ("Implement OAuth2 login", 8, 75.0),
            ("Database optimization", 4, 100.0),
            ("Write API documentation", 6, 40.0),
            ("Bug fix: Login timeout", 2, 60.0),
            ("Mobile responsive fixes", 3, 55.0),
            ("Cloud infrastructure setup", 10, 120.0),
            ("User feedback analysis", 5, 45.0),
            ("Security audit", 7, 90.0),
            ("Performance profiling", 4, 85.0),
        ]

        for idx, (task_name, items_count, rate) in enumerate(tasks):
            # Rotate through freelancers
            freelancer = db_freelancers[idx % len(db_freelancers)]
            
            wl = WorkLog(
                task_name=task_name,
                freelancer_id=freelancer.id,
                status=WorkLogStatus.PENDING
            )
            session.add(wl)
            session.flush() # Get ID

            # Add time entries
            for i in range(items_count):
                te = TimeEntry(
                    worklog_id=wl.id,
                    date=date.today() - timedelta(days=i),
                    hours=1.5 + (i % 3),
                    hourly_rate=rate,
                    description=f"Automated work on {task_name} segment {i+1}"
                )
                session.add(te)

        session.commit()
        logger.info("Successfully seeded worklogs across 5 different users.")

if __name__ == "__main__":
    seed_worklogs()
