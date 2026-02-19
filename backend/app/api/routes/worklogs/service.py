import logging
import uuid
from datetime import date, datetime, time

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    TimeEntry,
    TimeEntryPublic,
    User,
    Worklog,
    WorklogCreate,
    WorklogDetail,
    WorklogPublic,
    WorklogsPublic,
)

logger = logging.getLogger(__name__)


class WorklogService:
    @staticmethod
    def list_worklogs(
        session: Session,
        current_user: User,
        skip: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
    ) -> WorklogsPublic:
        base = (
            select(
                Worklog,
                func.coalesce(func.sum(TimeEntry.hours), 0.0).label("total_hours"),
                func.coalesce(
                    func.sum(TimeEntry.hours * Worklog.hourly_rate), 0.0
                ).label("total_earned"),
            )
            .outerjoin(TimeEntry, TimeEntry.worklog_id == Worklog.id)
            .group_by(Worklog.id)
        )

        if not current_user.is_superuser:
            base = base.where(Worklog.freelancer_id == current_user.id)

        if date_from:
            base = base.where(
                TimeEntry.start_time >= datetime.combine(date_from, time.min)
            )
        if date_to:
            base = base.where(
                TimeEntry.start_time <= datetime.combine(date_to, time.max)
            )

        count_stmt = select(func.count(func.distinct(Worklog.id))).select_from(
            Worklog
        )
        if not current_user.is_superuser:
            count_stmt = count_stmt.where(Worklog.freelancer_id == current_user.id)

        if date_from or date_to:
            count_stmt = count_stmt.join(
                TimeEntry, TimeEntry.worklog_id == Worklog.id
            )
            if date_from:
                count_stmt = count_stmt.where(
                    TimeEntry.start_time >= datetime.combine(date_from, time.min)
                )
            if date_to:
                count_stmt = count_stmt.where(
                    TimeEntry.start_time <= datetime.combine(date_to, time.max)
                )

        try:
            count = session.exec(count_stmt).one()
        except Exception:
            count = 0

        statement = base.order_by(Worklog.created_at.desc()).offset(skip).limit(limit)

        try:
            rows = session.execute(statement).all()
        except Exception as exc:
            logger.error("Failed to list worklogs: %s", exc)
            return WorklogsPublic(data=[], count=0)

        result = []
        for row in rows:
            wl: Worklog = row[0]
            total_hours: float = row[1]
            total_earned: float = row[2]
            try:
                freelancer_name = wl.freelancer.full_name if wl.freelancer else None
            except Exception:
                freelancer_name = None

            result.append(
                WorklogPublic(
                    id=wl.id,
                    title=wl.title,
                    description=wl.description,
                    freelancer_id=wl.freelancer_id,
                    freelancer_name=freelancer_name,
                    hourly_rate=wl.hourly_rate,
                    total_hours=round(total_hours, 2),
                    total_earned=round(total_earned, 2),
                    created_at=wl.created_at,
                )
            )

        return WorklogsPublic(data=result, count=count)

    @staticmethod
    def get_worklog(
        session: Session, current_user: User, worklog_id: uuid.UUID
    ) -> WorklogDetail:
        wl = session.get(Worklog, worklog_id)
        if not wl:
            raise HTTPException(status_code=404, detail="Worklog not found")
        if not current_user.is_superuser and wl.freelancer_id != current_user.id:
            raise HTTPException(status_code=400, detail="Not enough permissions")

        try:
            entries = session.exec(
                select(TimeEntry)
                .where(TimeEntry.worklog_id == worklog_id)
                .order_by(TimeEntry.start_time.desc())
            ).all()
        except Exception as exc:
            logger.error("Failed to load time entries for worklog %s: %s", worklog_id, exc)
            entries = []

        total_hours = round(sum(e.hours for e in entries), 2)
        total_earned = round(total_hours * wl.hourly_rate, 2)

        try:
            freelancer_name = wl.freelancer.full_name if wl.freelancer else None
        except Exception:
            freelancer_name = None

        return WorklogDetail(
            id=wl.id,
            title=wl.title,
            description=wl.description,
            freelancer_id=wl.freelancer_id,
            freelancer_name=freelancer_name,
            hourly_rate=wl.hourly_rate,
            total_hours=total_hours,
            total_earned=total_earned,
            created_at=wl.created_at,
            time_entries=[
                TimeEntryPublic(
                    id=e.id,
                    worklog_id=e.worklog_id,
                    start_time=e.start_time,
                    end_time=e.end_time,
                    description=e.description,
                    hours=e.hours,
                    created_at=e.created_at,
                )
                for e in entries
            ],
        )

    @staticmethod
    def create_worklog(
        session: Session, current_user: User, worklog_in: WorklogCreate
    ) -> WorklogPublic:
        wl = Worklog(
            title=worklog_in.title,
            description=worklog_in.description,
            freelancer_id=current_user.id,
            hourly_rate=current_user.hourly_rate or 0.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(wl)
        session.commit()
        session.refresh(wl)

        return WorklogPublic(
            id=wl.id,
            title=wl.title,
            description=wl.description,
            freelancer_id=wl.freelancer_id,
            freelancer_name=current_user.full_name,
            hourly_rate=wl.hourly_rate,
            total_hours=0.0,
            total_earned=0.0,
            created_at=wl.created_at,
        )
