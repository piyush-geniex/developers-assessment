"""
Worklogs API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from sqlalchemy import and_
from typing import List, Optional
from datetime import date
from decimal import Decimal
import uuid

from ..database import get_session
from ..models import (
    Worklog, Freelancer, Task, TimeEntry,
    WorklogRead, WorklogWithDetails, TimeEntryRead,
    FreelancerRead, TaskRead
)

router = APIRouter(prefix="/api/worklogs", tags=["worklogs"])


@router.get("", response_model=List[WorklogRead])
async def get_worklogs(
    date_from: Optional[date] = Query(None, description="Filter worklogs from this date"),
    date_to: Optional[date] = Query(None, description="Filter worklogs until this date"),
    status: Optional[str] = Query(None, description="Filter by status (pending, paid, cancelled)"),
    freelancer_id: Optional[uuid.UUID] = Query(None, description="Filter by freelancer ID"),
    session: Session = Depends(get_session)
) -> List[WorklogRead]:
    """
    Get all worklogs with optional filtering.
    Returns worklogs with freelancer name, task title, and time entries count.
    """
    # Build the query with joins
    statement = (
        select(
            Worklog,
            Freelancer.name.label("freelancer_name"),
            Freelancer.email.label("freelancer_email"),
            Freelancer.hourly_rate.label("freelancer_hourly_rate"),
            Task.title.label("task_title"),
        )
        .join(Freelancer, Worklog.freelancer_id == Freelancer.id)
        .join(Task, Worklog.task_id == Task.id)
    )
    
    # Apply filters
    conditions = []
    if date_from:
        conditions.append(func.date(Worklog.created_at) >= date_from)
    if date_to:
        conditions.append(func.date(Worklog.created_at) <= date_to)
    if status:
        conditions.append(Worklog.status == status)
    if freelancer_id:
        conditions.append(Worklog.freelancer_id == freelancer_id)
    
    if conditions:
        statement = statement.where(and_(*conditions))
    
    statement = statement.order_by(Worklog.created_at.desc())
    
    results = session.exec(statement).all()
    
    # Get time entries count for each worklog
    worklogs = []
    for row in results:
        worklog = row[0]
        
        # Count time entries
        count_stmt = select(func.count(TimeEntry.id)).where(TimeEntry.worklog_id == worklog.id)
        time_entries_count = session.exec(count_stmt).first() or 0
        
        worklog_data = WorklogRead(
            id=worklog.id,
            freelancer_id=worklog.freelancer_id,
            task_id=worklog.task_id,
            description=worklog.description,
            total_hours=worklog.total_hours,
            total_amount=worklog.total_amount,
            status=worklog.status,
            created_at=worklog.created_at,
            freelancer_name=row.freelancer_name,
            freelancer_email=row.freelancer_email,
            freelancer_hourly_rate=row.freelancer_hourly_rate,
            task_title=row.task_title,
            time_entries_count=time_entries_count
        )
        worklogs.append(worklog_data)
    
    return worklogs


@router.get("/eligible", response_model=List[WorklogRead])
async def get_eligible_worklogs(
    date_from: date = Query(..., description="Start date for eligibility"),
    date_to: date = Query(..., description="End date for eligibility"),
    session: Session = Depends(get_session)
) -> List[WorklogRead]:
    """
    Get worklogs eligible for payment within the specified date range.
    Only returns worklogs with status 'pending'.
    """
    statement = (
        select(
            Worklog,
            Freelancer.name.label("freelancer_name"),
            Freelancer.email.label("freelancer_email"),
            Freelancer.hourly_rate.label("freelancer_hourly_rate"),
            Task.title.label("task_title"),
        )
        .join(Freelancer, Worklog.freelancer_id == Freelancer.id)
        .join(Task, Worklog.task_id == Task.id)
        .where(
            and_(
                Worklog.status == "pending",
                func.date(Worklog.created_at) >= date_from,
                func.date(Worklog.created_at) <= date_to
            )
        )
        .order_by(Worklog.created_at.desc())
    )
    
    results = session.exec(statement).all()
    
    worklogs = []
    for row in results:
        worklog = row[0]
        
        count_stmt = select(func.count(TimeEntry.id)).where(TimeEntry.worklog_id == worklog.id)
        time_entries_count = session.exec(count_stmt).first() or 0
        
        worklog_data = WorklogRead(
            id=worklog.id,
            freelancer_id=worklog.freelancer_id,
            task_id=worklog.task_id,
            description=worklog.description,
            total_hours=worklog.total_hours,
            total_amount=worklog.total_amount,
            status=worklog.status,
            created_at=worklog.created_at,
            freelancer_name=row.freelancer_name,
            freelancer_email=row.freelancer_email,
            freelancer_hourly_rate=row.freelancer_hourly_rate,
            task_title=row.task_title,
            time_entries_count=time_entries_count
        )
        worklogs.append(worklog_data)
    
    return worklogs


@router.get("/{worklog_id}", response_model=WorklogWithDetails)
async def get_worklog(
    worklog_id: uuid.UUID,
    session: Session = Depends(get_session)
) -> WorklogWithDetails:
    """
    Get a specific worklog with all time entries and related details.
    """
    worklog = session.get(Worklog, worklog_id)
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")
    
    # Get related entities
    freelancer = session.get(Freelancer, worklog.freelancer_id)
    task = session.get(Task, worklog.task_id)
    
    # Get time entries
    time_entries_stmt = (
        select(TimeEntry)
        .where(TimeEntry.worklog_id == worklog_id)
        .order_by(TimeEntry.start_time)
    )
    time_entries = session.exec(time_entries_stmt).all()
    
    return WorklogWithDetails(
        id=worklog.id,
        freelancer_id=worklog.freelancer_id,
        task_id=worklog.task_id,
        description=worklog.description,
        total_hours=worklog.total_hours,
        total_amount=worklog.total_amount,
        status=worklog.status,
        created_at=worklog.created_at,
        freelancer=FreelancerRead.model_validate(freelancer) if freelancer else None,
        task=TaskRead.model_validate(task) if task else None,
        time_entries=[TimeEntryRead.model_validate(te) for te in time_entries]
    )
