import uuid
from datetime import datetime, timezone
from typing import Any, List

from fastapi import HTTPException
from sqlalchemy import delete, update
from sqlmodel import Session, func, select, col
from decimal import Decimal

from app.models import WorkLogEntry

from app.models import (
    Task,
    TaskCreate,
    TaskItem,
    TaskItems,
    TaskUpdate,
    Message,
)


class TaskService:
    @staticmethod
    def get_tasks(
        session: Session,
        current_user: Any,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> TaskItems:
        """
        Retrieve tasks with optional date filtering.
        """
        # Adjust end_date to be at 23:59:59 of that day for inclusive filtering
        if end_date is not None:
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        base_where = None
        # count tasks
        if current_user.is_superuser:
            count_statement = select(func.count()).select_from(Task)
        else:
            count_statement = (
                select(func.count())
                .select_from(Task)
                .where(Task.created_by_id == current_user.id)
            )
            base_where = (Task.created_by_id == current_user.id)

        # Apply date filters to count
        if start_date is not None:
            count_statement = count_statement.where(Task.created_at >= start_date)
        if end_date is not None:
            count_statement = count_statement.where(Task.created_at <= end_date)

        count = session.exec(count_statement).one()

        # aggregated query: fetch tasks with sum(amount) in one query
        total_col = func.coalesce(func.sum(WorkLogEntry.amount), 0).label("total")
        agg_stmt = (
            select(Task, total_col)
            .select_from(Task)
            .outerjoin(WorkLogEntry, WorkLogEntry.task_id == Task.id)
            .group_by(Task.id)
        )
        if base_where is not None:
            agg_stmt = agg_stmt.where(base_where)

        # Apply date filters
        if start_date is not None:
            agg_stmt = agg_stmt.where(Task.created_at >= start_date)
        if end_date is not None:
            agg_stmt = agg_stmt.where(Task.created_at <= end_date)

        agg_stmt = agg_stmt.order_by(Task.created_at.desc()).offset(skip).limit(limit)

        rows = session.exec(agg_stmt).all()
        tasks: list[TaskItem] = []
        for task_obj, total in rows:
            task_item = TaskItem.model_validate(task_obj)
            task_item.total_amount = Decimal(total) if total is not None else Decimal("0.0")
            tasks.append(task_item)

        return TaskItems(data=tasks, count=count)

    @staticmethod
    def get_task(session: Session, current_user: Any, task_id: uuid.UUID) -> TaskItem:
        """
        Get task by ID.
        """
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if not current_user.is_superuser and (task.created_by_id != current_user.id):
            raise HTTPException(status_code=400, detail="Not enough permissions")
        # compute total amount for task
        sum_stmt = select(func.coalesce(func.sum(WorkLogEntry.amount), 0)).where(
            WorkLogEntry.task_id == task.id
        )
        total = session.exec(sum_stmt).one()
        task_item = TaskItem.model_validate(task)
        task_item.total_amount = Decimal(total) if total is not None else Decimal("0.0")
        return task_item

    @staticmethod
    def create_task(
        session: Session, current_user: Any, task_in: TaskCreate
    ) -> TaskItem:
        """
        Create new task.
        """

        task = Task.model_validate(
            task_in,
            update={"created_by_id": current_user.id, "created_at": datetime.now(timezone.utc)},
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def update_task(
        session: Session, current_user: Any, task_id: uuid.UUID, task_in: TaskUpdate
    ) -> TaskItem:
        """
        Update a task.
        """
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if not current_user.is_superuser and (task.created_by_id != current_user.id):
            raise HTTPException(status_code=400, detail="Not enough permissions")

        update_dict = task_in.model_dump(exclude_unset=True)
        update_dict["edited_by_id"] = current_user.id
        update_dict["edited_at"] = datetime.now(timezone.utc)

        task.sqlmodel_update(update_dict)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def delete_task(
        session: Session, current_user: Any, task_id: uuid.UUID
    ) -> Message:
        """
        Delete a task.
        """
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if not current_user.is_superuser and (task.created_by_id != current_user.id):
            raise HTTPException(status_code=400, detail="Not enough permissions")
        session.delete(task)
        session.commit()
        return Message(message="Task deleted successfully")

    @staticmethod
    def initiate_payments(
        session: Session, current_user: Any, work_logs_in: List[uuid.UUID]
    ) -> Message:
        """
        Bulk initiate payment for a list of work log entries.
        """

        stmt = (
            update(WorkLogEntry)
            .where(col(WorkLogEntry.id).in_(work_logs_in))
            .values(
                payment_initiated=True,
                payment_initiated_date=datetime.now(timezone.utc),
                initiated_by_id=current_user.id,
                edited_by_id=current_user.id,
                edited_at=datetime.now(timezone.utc),
            )
        )

        result = session.exec(stmt)

        session.commit()
        return Message(message=f"Payment initiated for {result.rowcount} selected work log entries")

    @staticmethod
    def bulk_delete_work_logs(
        session: Session, work_logs_in: List[uuid.UUID]
    ) -> Message:
        """
        Bulk delete for a list of work log entries.
        """

        stmt = (
            delete(WorkLogEntry)
            .where(col(WorkLogEntry.id).in_(work_logs_in))
        )

        result = session.exec(stmt)

        session.commit()
        return Message(message=f"Deleted {result.rowcount} selected work log entries")
