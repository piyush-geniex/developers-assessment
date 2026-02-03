import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.time_entries.service import TimeEntryService
from app.models import (
    Message,
    TimeEntryCreate,
    TimeEntryPublic,
    TimeEntriesPublic,
    TimeEntryUpdate,
)

router = APIRouter(prefix="/time-entries", tags=["time-entries"])


@router.get("/", response_model=TimeEntriesPublic)
def read_time_entries(
    session: SessionDep,
    current_user: CurrentUser,
    work_log_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve time entries with optional filtering by worklog.
    """
    return TimeEntryService.get_time_entries(session, work_log_id, skip, limit)


@router.get("/{entry_id}", response_model=TimeEntryPublic)
def read_time_entry(
    session: SessionDep,
    current_user: CurrentUser,
    entry_id: uuid.UUID,
) -> Any:
    """
    Get a time entry by ID.
    """
    return TimeEntryService.get_time_entry(session, entry_id)


@router.post("/", response_model=TimeEntryPublic)
def create_time_entry(
    session: SessionDep,
    current_user: CurrentUser,
    entry_in: TimeEntryCreate,
) -> Any:
    """
    Create a new time entry.
    """
    return TimeEntryService.create_time_entry(session, entry_in)


@router.patch("/{entry_id}", response_model=TimeEntryPublic)
def update_time_entry(
    session: SessionDep,
    current_user: CurrentUser,
    entry_id: uuid.UUID,
    entry_in: TimeEntryUpdate,
) -> Any:
    """
    Update a time entry.
    """
    return TimeEntryService.update_time_entry(session, entry_id, entry_in)


@router.delete("/{entry_id}")
def delete_time_entry(
    session: SessionDep,
    current_user: CurrentUser,
    entry_id: uuid.UUID,
) -> Message:
    """
    Delete a time entry.
    """
    TimeEntryService.delete_time_entry(session, entry_id)
    return Message(message="Time entry deleted successfully")
