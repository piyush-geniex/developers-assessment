from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import Task, TimeEntry, User, UserCreate, Worklog

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

    first_task = session.exec(select(Task)).first()
    if first_task is None:
        _seed_worklogs(session, user.id)


def _seed_worklogs(session: Session, owner_id) -> None:
    t1 = Task(name="API integration")
    session.add(t1)
    session.commit()
    session.refresh(t1)
    t2 = Task(name="Dashboard UI")
    session.add(t2)
    session.commit()
    session.refresh(t2)
    t3 = Task(name="Database migration")
    session.add(t3)
    session.commit()
    session.refresh(t3)

    w1 = Worklog(task_id=t1.id, owner_id=owner_id, amount_earned=1250.0, status="pending")
    session.add(w1)
    session.commit()
    session.refresh(w1)
    w2 = Worklog(task_id=t1.id, owner_id=owner_id, amount_earned=800.0, status="pending")
    session.add(w2)
    session.commit()
    session.refresh(w2)
    w3 = Worklog(task_id=t2.id, owner_id=owner_id, amount_earned=2100.0, status="pending")
    session.add(w3)
    session.commit()
    session.refresh(w3)

    session.add(TimeEntry(worklog_id=w1.id, description="Setup and auth", hours=5, rate=100, amount=500))
    session.add(TimeEntry(worklog_id=w1.id, description="Endpoints implementation", hours=7.5, rate=100, amount=750))
    session.add(TimeEntry(worklog_id=w2.id, description="Review and fixes", hours=8, rate=100, amount=800))
    session.add(TimeEntry(worklog_id=w3.id, description="Layout", hours=10, rate=100, amount=1000))
    session.add(TimeEntry(worklog_id=w3.id, description="Charts", hours=11, rate=100, amount=1100))
    session.commit()
