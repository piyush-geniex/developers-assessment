from datetime import datetime

from sqlmodel import Session, select, func

from app.models import TimeEntry, Task, User, WorklogSummary


class WorklogService:
    @staticmethod
    def get_worklog_summary(
        session: Session,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[WorklogSummary]:
        statement = (
            select(
                TimeEntry.task_id,
                Task.title.label("task_title"),
                TimeEntry.freelancer_id,
                User.full_name.label("freelancer_name"),
                func.count(TimeEntry.id).label("entry_count"),
            )
            .join(Task, TimeEntry.task_id == Task.id)
            .join(User, TimeEntry.freelancer_id == User.id)
            .group_by(
                TimeEntry.task_id,
                Task.title,
                TimeEntry.freelancer_id,
                User.full_name,
                User.hourly_rate,
            )
        )

        if date_from:
            statement = statement.where(TimeEntry.start_time >= date_from)
        if date_to:
            statement = statement.where(TimeEntry.end_time <= date_to)

        results = session.exec(statement).all()

        summaries = []
        for result in results:
            task_id, task_title, freelancer_id, freelancer_name, entry_count = result

            hours_statement = (
                select(
                    func.sum(
                        func.extract("epoch", TimeEntry.end_time - TimeEntry.start_time) / 3600
                    )
                )
                .where(TimeEntry.task_id == task_id)
                .where(TimeEntry.freelancer_id == freelancer_id)
            )

            if date_from:
                hours_statement = hours_statement.where(TimeEntry.start_time >= date_from)
            if date_to:
                hours_statement = hours_statement.where(TimeEntry.end_time <= date_to)

            total_hours = float(session.exec(hours_statement).one() or 0.0)

            user = session.get(User, freelancer_id)
            hourly_rate = float(user.hourly_rate) if user and user.hourly_rate else 0.0
            total_amount = total_hours * hourly_rate

            summaries.append(
                WorklogSummary(
                    task_id=task_id,
                    task_title=task_title,
                    freelancer_id=freelancer_id,
                    freelancer_name=freelancer_name or "Unknown",
                    total_hours=round(total_hours, 2),
                    total_amount=round(total_amount, 2),
                    entry_count=entry_count,
                )
            )

        return summaries
