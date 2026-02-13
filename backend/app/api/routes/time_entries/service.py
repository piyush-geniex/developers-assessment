from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import TimeEntry, TimeEntryCreate, TimeEntryUpdate, User


class TimeEntryService:
    @staticmethod
    def get_time_entries(
        session: Session, current_user: User, skip: int = 0, limit: int = 100
    ) -> list[TimeEntry]:
        if current_user.is_superuser:
            statement = select(TimeEntry).offset(skip).limit(limit)
        else:
            statement = (
                select(TimeEntry)
                .where(TimeEntry.freelancer_id == current_user.id)
                .offset(skip)
                .limit(limit)
            )
        return list(session.exec(statement).all())

    @staticmethod
    def create_time_entry(
        session: Session, current_user: User, time_entry_in: TimeEntryCreate
    ) -> TimeEntry:
        if time_entry_in.start_time >= time_entry_in.end_time:
            raise HTTPException(
                status_code=400, detail="Start time must be before end time"
            )

        db_time_entry = TimeEntry.model_validate(
            time_entry_in, update={"freelancer_id": current_user.id}
        )
        session.add(db_time_entry)
        session.commit()
        session.refresh(db_time_entry)
        return db_time_entry

    @staticmethod
    def get_time_entry(session: Session, time_entry_id: UUID) -> TimeEntry:
        time_entry = session.get(TimeEntry, time_entry_id)
        if not time_entry:
            raise HTTPException(status_code=404, detail="Time entry not found")
        return time_entry

    @staticmethod
    def update_time_entry(
        session: Session,
        current_user: User,
        time_entry_id: UUID,
        time_entry_in: TimeEntryUpdate,
    ) -> TimeEntry:
        db_time_entry = TimeEntryService.get_time_entry(session, time_entry_id)

        if not current_user.is_superuser and db_time_entry.freelancer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        update_dict = time_entry_in.model_dump(exclude_unset=True)

        if "start_time" in update_dict or "end_time" in update_dict:
            start = update_dict.get("start_time", db_time_entry.start_time)
            end = update_dict.get("end_time", db_time_entry.end_time)
            if start >= end:
                raise HTTPException(
                    status_code=400, detail="Start time must be before end time"
                )

        db_time_entry.sqlmodel_update(update_dict)
        session.add(db_time_entry)
        session.commit()
        session.refresh(db_time_entry)
        return db_time_entry

    @staticmethod
    def delete_time_entry(
        session: Session, current_user: User, time_entry_id: UUID
    ) -> None:
        db_time_entry = TimeEntryService.get_time_entry(session, time_entry_id)

        if not current_user.is_superuser and db_time_entry.freelancer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        session.delete(db_time_entry)
        session.commit()
