import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import Message, Task, TaskCreate, TaskPublic, TasksPublic, TaskUpdate


class TaskService:
    @staticmethod
    def get_tasks(session: Session, skip: int = 0, limit: int = 100) -> TasksPublic:
        count_statement = select(func.count()).select_from(Task)
        count = session.exec(count_statement).one()
        statement = select(Task).offset(skip).limit(limit).order_by(Task.created_at.desc())
        tasks = session.exec(statement).all()

        return TasksPublic(data=tasks, count=count)

    @staticmethod
    def get_task(session: Session, task_id: uuid.UUID) -> TaskPublic:
        task = session.get(Task, task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return task

    @staticmethod
    def create_task(session: Session, task_in: TaskCreate) -> TaskPublic:
        task = Task.model_validate(task_in)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def update_task(session: Session, task_id: uuid.UUID, task_in: TaskUpdate) -> TaskPublic:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        update_dict = task_in.model_dump(exclude_unset=True)
        task.sqlmodel_update(update_dict)
        task.updated_at = datetime.utcnow()
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def delete_task(session: Session, task_id: uuid.UUID) -> Message:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        session.delete(task)
        session.commit()
        return Message(message="Task deleted successfully")
