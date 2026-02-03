from datetime import datetime

from sqlmodel import Session, create_engine, text

from app.core.config import settings
from app.models import Freelancer, Task, TimeEntry

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def seed_data() -> None:
    with Session(engine) as session:
        # Clear existing data
        print("Clearing existing data...")
        session.exec(text("DELETE FROM timeentry"))
        session.exec(text("DELETE FROM task"))
        session.exec(text("DELETE FROM freelancer"))
        session.commit()
        print("Existing data cleared.")

        dt_now = datetime.utcnow().isoformat()

        fl1 = Freelancer(
            name="Alice Johnson",
            email="alice@example.com",
            hourly_rate=50.0,
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(fl1)
        session.commit()
        session.refresh(fl1)

        fl2 = Freelancer(
            name="Bob Smith",
            email="bob@example.com",
            hourly_rate=75.0,
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(fl2)
        session.commit()
        session.refresh(fl2)

        tsk1 = Task(
            name="Build Authentication",
            description="Implement user login and registration",
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(tsk1)
        session.commit()
        session.refresh(tsk1)

        tsk2 = Task(
            name="API Integration",
            description="Connect frontend to backend APIs",
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(tsk2)
        session.commit()
        session.refresh(tsk2)

        ent1 = TimeEntry(
            freelancer_id=fl1.id,
            task_id=tsk1.id,
            hours=5.0,
            description="Setup auth routes",
            logged_at="2026-01-15",
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(ent1)
        session.commit()

        ent2 = TimeEntry(
            freelancer_id=fl1.id,
            task_id=tsk1.id,
            hours=3.5,
            description="Add JWT tokens",
            logged_at="2026-01-16",
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(ent2)
        session.commit()

        ent3 = TimeEntry(
            freelancer_id=fl2.id,
            task_id=tsk2.id,
            hours=8.0,
            description="Connect API endpoints",
            logged_at="2026-01-20",
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(ent3)
        session.commit()

        ent4 = TimeEntry(
            freelancer_id=fl2.id,
            task_id=tsk2.id,
            hours=4.0,
            description="Handle errors",
            logged_at="2026-01-21",
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(ent4)
        session.commit()

        # Add more freelancers
        fl3 = Freelancer(
            name="Carol Davis",
            email="carol@example.com",
            hourly_rate=60.0,
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(fl3)
        session.commit()
        session.refresh(fl3)

        fl4 = Freelancer(
            name="David Wilson",
            email="david@example.com",
            hourly_rate=85.0,
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(fl4)
        session.commit()
        session.refresh(fl4)

        # Add more tasks
        tsk3 = Task(
            name="Database Migration",
            description="Migrate from PostgreSQL to MongoDB",
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(tsk3)
        session.commit()
        session.refresh(tsk3)

        tsk4 = Task(
            name="UI Redesign",
            description="Modernize dashboard interface",
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(tsk4)
        session.commit()
        session.refresh(tsk4)

        tsk5 = Task(
            name="Payment Integration",
            description="Integrate Stripe payment gateway",
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(tsk5)
        session.commit()
        session.refresh(tsk5)

        # Add more time entries with varied dates
        # Carol working on Database Migration
        session.add(
            TimeEntry(
                freelancer_id=fl3.id,
                task_id=tsk3.id,
                hours=6.0,
                description="Schema analysis",
                logged_at="2026-01-22",
                created_at=dt_now,
                updated_at=dt_now,
            )
        )
        session.add(
            TimeEntry(
                freelancer_id=fl3.id,
                task_id=tsk3.id,
                hours=7.5,
                description="Data migration scripts",
                logged_at="2026-01-23",
                created_at=dt_now,
                updated_at=dt_now,
            )
        )

        # David working on UI Redesign
        session.add(
            TimeEntry(
                freelancer_id=fl4.id,
                task_id=tsk4.id,
                hours=5.5,
                description="Wireframe design",
                logged_at="2026-01-24",
                created_at=dt_now,
                updated_at=dt_now,
            )
        )
        session.add(
            TimeEntry(
                freelancer_id=fl4.id,
                task_id=tsk4.id,
                hours=8.0,
                description="Component implementation",
                logged_at="2026-01-25",
                created_at=dt_now,
                updated_at=dt_now,
            )
        )

        # Alice also working on Payment Integration
        session.add(
            TimeEntry(
                freelancer_id=fl1.id,
                task_id=tsk5.id,
                hours=4.5,
                description="Stripe API setup",
                logged_at="2026-01-26",
                created_at=dt_now,
                updated_at=dt_now,
            )
        )
        session.add(
            TimeEntry(
                freelancer_id=fl1.id,
                task_id=tsk5.id,
                hours=3.0,
                description="Webhook configuration",
                logged_at="2026-01-27",
                created_at=dt_now,
                updated_at=dt_now,
            )
        )

        # Bob also working on Payment Integration
        session.add(
            TimeEntry(
                freelancer_id=fl2.id,
                task_id=tsk5.id,
                hours=6.0,
                description="Frontend integration",
                logged_at="2026-01-28",
                created_at=dt_now,
                updated_at=dt_now,
            )
        )

        # Carol working on API Integration too
        session.add(
            TimeEntry(
                freelancer_id=fl3.id,
                task_id=tsk2.id,
                hours=5.0,
                description="API testing",
                logged_at="2026-01-29",
                created_at=dt_now,
                updated_at=dt_now,
            )
        )

        session.commit()

        print("Seed data created successfully!")
        print(f"Freelancers: 4 ({fl1.name}, {fl2.name}, {fl3.name}, {fl4.name})")
        print(f"Tasks: 5 tasks created")
        print(f"Time entries: 12 entries created")
        print(f"Total hours: ~60 hours")
        print(f"Total amount: ~$4,500")


if __name__ == "__main__":
    seed_data()
