import logging


from sqlmodel import Session
from sqlmodel import Session, select
from app.core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        init_worklogs(session)


def init_worklogs(session: Session) -> None:
    from app.models import User, WorkLog, TimeEntry
    from app.core.config import settings
    from datetime import datetime, timedelta
    import random

    # Get the superuser to assign tasks to (or create a new freelancer)
    user = session.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
    if not user:
        return

    # Check if we already have worklogs
    existing_logs = session.exec(select(WorkLog)).first()
    if existing_logs:
        return

    print("Seeding WorkLogs and TimeEntries...")
    
    tasks = ["Frontend Development", "Backend API", "Database Design", "Unit Testing", "Deployment Ops"]
    
    for i in range(5):
        # Create a worklog
        wl = WorkLog(
            freelancer_id=user.id,
            task_name=tasks[i],
            status=random.choice(["pending", "paid", "pending"]) # More pending for testing
        )
        session.add(wl)
        session.commit()
        session.refresh(wl)
        
        # Create time entries
        for j in range(random.randint(2, 5)):
            start = datetime.utcnow() - timedelta(days=random.randint(1, 10), hours=random.randint(1, 5))
            duration = random.randint(1, 4)
            end = start + timedelta(hours=duration)
            
            te = TimeEntry(
                worklog_id=wl.id,
                start_time=start,
                end_time=end,
                description=f"Worked on {tasks[i]} part {j+1}",
                rate=50.0 # $50/hr
            )
            session.add(te)
        
        session.commit()


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
