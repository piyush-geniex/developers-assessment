from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import (
    Task,
    TimeEntry,
    User,
    UserCreate,
    WorkLog,
)

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    # Seed demo tasks and worklogs if none exist
    if session.exec(select(Task)).first() is None:
        task1 = Task(title="API development", description="Backend API for payment dashboard")
        task2 = Task(title="Frontend dashboard", description="React admin UI for worklogs")
        task3 = Task(title="Database schema", description="Design and migrations")
        session.add(task1)
        session.add(task2)
        session.add(task3)
        session.commit()
        session.refresh(task1)
        session.refresh(task2)
        session.refresh(task3)
        for t in (task1, task2, task3):
            wl = WorkLog(task_id=t.id, user_id=user.id)
            session.add(wl)
        session.commit()
        for t in (task1, task2, task3):
            wl = session.exec(
                select(WorkLog).where(
                    WorkLog.task_id == t.id,
                    WorkLog.user_id == user.id,
                )
            ).first()
            if wl:
                session.add(
                    TimeEntry(
                        work_log_id=wl.id,
                        entry_date="2025-01-15",
                        duration_minutes=120,
                        amount_cents=24000,  # $240
                        description="Initial implementation",
                    )
                )
                session.add(
                    TimeEntry(
                        work_log_id=wl.id,
                        entry_date="2025-01-20",
                        duration_minutes=90,
                        amount_cents=18000,
                        description="Review and fixes",
                    )
                )
        session.commit()
