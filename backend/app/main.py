import os
from datetime import datetime, date
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session, select, func
from .models import User, Task, WorkLog, TimeEntry, PaymentBatch

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/worklog_db")
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI(title="WorkLog Payment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # Seed data if empty
    with Session(engine) as session:
        if not session.exec(select(User)).first():
            seed_data(session)

def seed_data(session: Session):
    admin = User(name="Admin User", email="admin@example.com", role="admin")
    freelancer1 = User(name="Alice Dev", email="alice@example.com", role="freelancer")
    freelancer2 = User(name="Bob Designer", email="bob@example.com", role="freelancer")
    session.add(admin)
    session.add(freelancer1)
    session.add(freelancer2)
    session.commit()
    
    task1 = Task(title="Frontend Development", rate_per_hour=50.0)
    task2 = Task(title="UI Design", rate_per_hour=40.0)
    session.add(task1)
    session.add(task2)
    session.commit()
    
    wl1 = WorkLog(task_id=task1.id, freelancer_id=freelancer1.id)
    wl2 = WorkLog(task_id=task2.id, freelancer_id=freelancer2.id)
    session.add(wl1)
    session.add(wl2)
    session.commit()
    
    te1 = TimeEntry(worklog_id=wl1.id, date=datetime(2026, 2, 1), hours=4, description="Coded dashboard layout")
    te2 = TimeEntry(worklog_id=wl1.id, date=datetime(2026, 2, 2), hours=5, description="Integrated API")
    te3 = TimeEntry(worklog_id=wl2.id, date=datetime(2026, 2, 1), hours=8, description="Designed mockups")
    session.add(te1)
    session.add(te2)
    session.add(te3)
    session.commit()

def get_session():
    with Session(engine) as session:
        yield session

@app.get("/worklogs")
def get_worklogs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session: Session = Depends(get_session)
):
    query = select(WorkLog)
    
    # This is a bit simplified; real filtering might need to join with TimeEntry
    worklogs = session.exec(query).all()
    
    results = []
    for wl in worklogs:
        # Filter time entries by date range if provided
        entries = wl.time_entries
        if start_date:
            entries = [e for e in entries if e.date.date() >= start_date]
        if end_date:
            entries = [e for e in entries if e.date.date() <= end_date]
        
        if not entries and (start_date or end_date):
            continue

        total_hours = sum(e.hours for e in entries)
        total_earned = total_hours * wl.task.rate_per_hour
        
        results.append({
            "id": wl.id,
            "freelancer_name": wl.freelancer.name,
            "task_title": wl.task.title,
            "total_hours": total_hours,
            "total_earned": total_earned,
            "status": wl.status,
            "rate": wl.task.rate_per_hour
        })
    
    return results

@app.get("/worklogs/{worklog_id}")
def get_worklog_details(worklog_id: int, session: Session = Depends(get_session)):
    wl = session.get(WorkLog, worklog_id)
    if not wl:
        raise HTTPException(status_code=404, detail="WorkLog not found")
    
    return {
        "id": wl.id,
        "freelancer": wl.freelancer,
        "task": wl.task,
        "time_entries": wl.time_entries,
        "status": wl.status
    }

@app.post("/payments")
def process_payments(worklog_ids: List[int], session: Session = Depends(get_session)):
    total_amount = 0
    processed_logs = []
    
    for wl_id in worklog_ids:
        wl = session.get(WorkLog, wl_id)
        if wl and wl.status != "paid":
            hours = sum(e.hours for e in wl.time_entries)
            amount = hours * wl.task.rate_per_hour
            total_amount += amount
            wl.status = "paid"
            session.add(wl)
            processed_logs.append(wl_id)
            
    if not processed_logs:
        raise HTTPException(status_code=400, detail="No eligible worklogs found for payment")
        
    batch = PaymentBatch(total_amount=total_amount)
    session.add(batch)
    session.commit()
    
    return {"message": "Payment processed successfully", "batch_id": batch.id, "total_paid": total_amount}
