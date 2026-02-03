"""
Seed script to create sample worklog data for testing

Run this script to populate the database with sample data:
    python seed_worklog_data.py

This will create:
- Sample worklogs with time segments
- Adjustments (positive and negative)
- Various scenarios to test the settlement system
"""
import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, create_engine, select

from app.api.routes.worklogs.models import Adjustment, TimeSegment, WorkLog
from app.core.config import settings
from app.models import User

# Create engine
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def seed_data():
    with Session(engine) as db:
        print("Starting data seeding...")
        
        # Get existing users (or create sample ones)
        users = db.exec(select(User).limit(2)).all()
        
        if len(users) < 2:
            print("Error: Need at least 2 users in database. Please create users first.")
            return
        
        user1 = users[0]
        user2 = users[1]
        
        print(f"Using User 1: {user1.email}")
        print(f"Using User 2: {user2.email}")
        
        # Scenario 1: Simple worklog with time segments (User 1)
        wl1 = WorkLog(
            id=uuid.uuid4(),
            user_id=user1.id,
            task_name="Backend API Development",
            created_at=datetime.utcnow() - timedelta(days=15)
        )
        db.add(wl1)
        db.commit()
        db.refresh(wl1)
        
        # Add time segments
        seg1 = TimeSegment(
            worklog_id=wl1.id,
            hours=10.0,
            rate=50.0,
            recorded_at=datetime.utcnow() - timedelta(days=14)
        )
        seg2 = TimeSegment(
            worklog_id=wl1.id,
            hours=8.0,
            rate=50.0,
            recorded_at=datetime.utcnow() - timedelta(days=13)
        )
        db.add(seg1)
        db.add(seg2)
        db.commit()
        
        print(f"✓ Created worklog '{wl1.task_name}' with 2 time segments (18 hrs @ $50 = $900)")
        
        # Scenario 2: Worklog with adjustment (User 1)
        wl2 = WorkLog(
            id=uuid.uuid4(),
            user_id=user1.id,
            task_name="Database Schema Design",
            created_at=datetime.utcnow() - timedelta(days=10)
        )
        db.add(wl2)
        db.commit()
        db.refresh(wl2)
        
        seg3 = TimeSegment(
            worklog_id=wl2.id,
            hours=12.0,
            rate=60.0,
            recorded_at=datetime.utcnow() - timedelta(days=9)
        )
        db.add(seg3)
        db.commit()
        
        # Add positive adjustment (bonus)
        adj1 = Adjustment(
            worklog_id=wl2.id,
            amount=100.0,
            reason="Excellent quality bonus",
            created_at=datetime.utcnow() - timedelta(days=8)
        )
        db.add(adj1)
        db.commit()
        
        print(f"✓ Created worklog '{wl2.task_name}' with segments and bonus (12 hrs @ $60 + $100 bonus = $820)")
        
        # Scenario 3: Worklog with negative adjustment (User 2)
        wl3 = WorkLog(
            id=uuid.uuid4(),
            user_id=user2.id,
            task_name="Frontend Development",
            created_at=datetime.utcnow() - timedelta(days=12)
        )
        db.add(wl3)
        db.commit()
        db.refresh(wl3)
        
        seg4 = TimeSegment(
            worklog_id=wl3.id,
            hours=20.0,
            rate=45.0,
            recorded_at=datetime.utcnow() - timedelta(days=11)
        )
        db.add(seg4)
        db.commit()
        
        # Add negative adjustment (deduction for rework)
        adj2 = Adjustment(
            worklog_id=wl3.id,
            amount=-150.0,
            reason="Rework required due to bugs",
            created_at=datetime.utcnow() - timedelta(days=7)
        )
        db.add(adj2)
        db.commit()
        
        print(f"✓ Created worklog '{wl3.task_name}' with deduction (20 hrs @ $45 - $150 = $750)")
        
        # Scenario 4: Worklog with removed segment (User 2)
        wl4 = WorkLog(
            id=uuid.uuid4(),
            user_id=user2.id,
            task_name="Code Review",
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        db.add(wl4)
        db.commit()
        db.refresh(wl4)
        
        seg5 = TimeSegment(
            worklog_id=wl4.id,
            hours=5.0,
            rate=40.0,
            recorded_at=datetime.utcnow() - timedelta(days=4)
        )
        seg6 = TimeSegment(
            worklog_id=wl4.id,
            hours=3.0,
            rate=40.0,
            recorded_at=datetime.utcnow() - timedelta(days=3),
            is_removed=True  # This segment is disputed/removed
        )
        db.add(seg5)
        db.add(seg6)
        db.commit()
        
        print(f"✓ Created worklog '{wl4.task_name}' with removed segment (5 hrs @ $40, 3 hrs removed = $200)")
        
        # Scenario 5: Recent worklog (User 1)
        wl5 = WorkLog(
            id=uuid.uuid4(),
            user_id=user1.id,
            task_name="API Testing",
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(wl5)
        db.commit()
        db.refresh(wl5)
        
        seg7 = TimeSegment(
            worklog_id=wl5.id,
            hours=6.0,
            rate=55.0,
            recorded_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(seg7)
        db.commit()
        
        print(f"✓ Created worklog '{wl5.task_name}' (6 hrs @ $55 = $330)")
        
        print("\n" + "="*60)
        print("DATA SEEDING COMPLETE!")
        print("="*60)
        print("\nSummary:")
        print(f"  User 1 ({user1.email}): 3 worklogs, Total: $2,050")
        print(f"  User 2 ({user2.email}): 2 worklogs, Total: $950")
        print("\nNext steps:")
        print("  1. Test list endpoint: GET /worklogs/list-all-worklogs")
        print("  2. Generate remittances: POST /worklogs/generate-remittances-for-all-users")
        print("  3. Check REMITTED status: GET /worklogs/list-all-worklogs?remittanceStatus=REMITTED")
        print("\nTo test retroactive scenarios:")
        print("  - Add more time segments to existing worklogs")
        print("  - Add adjustments (positive or negative)")
        print("  - Generate remittances again to see only new work settled")


if __name__ == "__main__":
    seed_data()
