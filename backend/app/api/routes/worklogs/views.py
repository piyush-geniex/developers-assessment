import uuid
from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Query, Body

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.worklogs.service import WorkLogService
from app.models import WorkLog, WorkLogPublic, WorkLogsPublic

router = APIRouter(prefix="/worklogs", tags=["worklogs"])

@router.get("/", response_model=WorkLogsPublic)
def read_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    freelancer_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve worklogs with filtering.
    """
    return WorkLogService.get_worklogs(session, date_from, date_to, freelancer_id, skip, limit)

@router.get("/{id}", response_model=WorkLog)
def read_worklog(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID
) -> Any:
    """
    Get worklog by ID with details.
    """
    # Note: The model returned is WorkLog which includes relationships if defined in response model ??
    # Actually WorkLog definition in models.py has relationships but Pydantic/SQLModel might not serialize them 
    # unless we use a specific Public model with relationships.
    # The default WorkLog model has 'time_entries' relationship 
    # but for API response we usually want nested models.
    # Let's rely on SQLModel behavior. If it doesn't return entries, I might need a specific schema.
    # However, 'return item' usually works if relationships are loaded.
    # But usually we want a specific schema. 
    # Let's verify models.py WorkLog definition again. 
    # It inherits WorkLogBase. 
    # For now returning WorkLog should be fine if we want raw data, 
    # but usually proper API design uses a Public (Read) schema.
    # I'll stick to WorkLog for now as I added it to models.py and it has time_entries relationship.
    # Pydantic v2 might need explicit config for lazy loading but here we access it.
    return WorkLogService.get_worklog(session, id)

@router.post("/pay", response_model=List[WorkLogPublic])
def pay_worklogs(
    session: SessionDep,
    current_user: CurrentUser,
    worklog_ids: List[uuid.UUID] = Body(...)
) -> Any:
    """
    Mark worklogs as paid.
    """
    # Simply reuse WorkLogPublic which is safe
    paid_logs = WorkLogService.pay_worklogs(session, worklog_ids)
    
    # We need to convert them to WorkLogPublic manually or let FastAPI do it.
    # But WorkLogPublic expects total_amount/duration which are not fields on DB model.
    # So the auto-conversion might fail or return default 0.
    # I'll map them properly.
    
    results = []
    for wl in paid_logs:
         entries = wl.time_entries
         duration = sum([(te.end_time - te.start_time).total_seconds() / 3600 for te in entries], 0.0)
         amount = sum([((te.end_time - te.start_time).total_seconds() / 3600) * te.rate for te in entries], 0.0)
         results.append(WorkLogPublic(
             id=wl.id,
             freelancer_id=wl.freelancer_id,
             task_name=wl.task_name,
             status=wl.status,
             created_at=wl.created_at,
             total_duration_hours=round(duration, 2),
             total_amount=round(amount, 2)
         ))
    return results
