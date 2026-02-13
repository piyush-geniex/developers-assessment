from typing import Any
from uuid import UUID

from fastapi import APIRouter
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    Task,
    TimeEntry,
    TimeEntryCreate,
    TimeEntryPublic,
    TimeEntriesPublic,
    TimeEntryUpdate,
    User,
)

from .service import TimeEntryService

router = APIRouter(prefix="/time-entries", tags=["time-entries"])


def _enrich_entry(session: Any, entry: TimeEntry) -> TimeEntryPublic:
    task = session.get(Task, entry.task_id)
    freelancer = session.get(User, entry.freelancer_id)
    entry_dict = entry.model_dump()
    entry_dict["task_title"] = task.title if task else "Unknown Task"
    entry_dict["freelancer_name"] = freelancer.full_name if freelancer and freelancer.full_name else "Unknown"
    return TimeEntryPublic(**entry_dict)


@router.get("/", response_model=TimeEntriesPublic)
def read_time_entries(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    count_statement = select(func.count()).select_from(TimeEntry)
    if not current_user.is_superuser:
        count_statement = count_statement.where(
            TimeEntry.freelancer_id == current_user.id
        )
    count = session.exec(count_statement).one()

    time_entries = TimeEntryService.get_time_entries(
        session=session, current_user=current_user, skip=skip, limit=limit
    )

    return TimeEntriesPublic(
        data=[_enrich_entry(session, e) for e in time_entries],
        count=count,
    )


@router.post("/", response_model=TimeEntryPublic)
def create_time_entry(
    session: SessionDep, current_user: CurrentUser, time_entry_in: TimeEntryCreate
) -> Any:
    entry = TimeEntryService.create_time_entry(
        session=session, current_user=current_user, time_entry_in=time_entry_in
    )
    return _enrich_entry(session, entry)


@router.get("/{id}", response_model=TimeEntryPublic)
def read_time_entry(session: SessionDep, current_user: CurrentUser, id: UUID) -> Any:
    entry = TimeEntryService.get_time_entry(session=session, time_entry_id=id)
    return _enrich_entry(session, entry)


@router.put("/{id}", response_model=TimeEntryPublic)
def update_time_entry(
    session: SessionDep,
    current_user: CurrentUser,
    id: UUID,
    time_entry_in: TimeEntryUpdate,
) -> Any:
    entry = TimeEntryService.update_time_entry(
        session=session,
        current_user=current_user,
        time_entry_id=id,
        time_entry_in=time_entry_in,
    )
    return _enrich_entry(session, entry)


@router.delete("/{id}", response_model=Message)
def delete_time_entry(
    session: SessionDep, current_user: CurrentUser, id: UUID
) -> Any:
    TimeEntryService.delete_time_entry(
        session=session, current_user=current_user, time_entry_id=id
    )
    return Message(message="Time entry deleted successfully")
