import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select

from app.api.deps import SessionDep
from app.models import Freelancer, Task, TimeEntry

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


class FreelancerCreate(BaseModel):
    name: str
    email: str
    hourly_rate: float

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value is None:
            raise ValueError("name is required")
        if not isinstance(value, str):
            raise ValueError("name must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("name cannot be empty")
        if len(value) > 255:
            raise ValueError("name too long")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if value is None:
            raise ValueError("email is required")
        if not isinstance(value, str):
            raise ValueError("email must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("email cannot be empty")
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", value):
            raise ValueError("email invalid format")
        return value

    @field_validator("hourly_rate")
    @classmethod
    def validate_hourly_rate(cls, value: float) -> float:
        if value is None:
            raise ValueError("hourly_rate is required")
        if not isinstance(value, (int, float)):
            raise ValueError("hourly_rate must be a number")
        if value <= 0:
            raise ValueError("hourly_rate must be positive")
        return float(value)


class TaskCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value is None:
            raise ValueError("name is required")
        if not isinstance(value, str):
            raise ValueError("name must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("name cannot be empty")
        if len(value) > 255:
            raise ValueError("name too long")
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("description must be a string")
        return value.strip()


class MarkPaidRequest(BaseModel):
    task_ids: list[int]
    payment_batch_id: str

    @field_validator("task_ids")
    @classmethod
    def validate_task_ids(cls, value: list[int]) -> list[int]:
        if value is None:
            raise ValueError("task_ids is required")
        if not isinstance(value, list):
            raise ValueError("task_ids must be a list")
        if len(value) == 0:
            raise ValueError("task_ids cannot be empty")
        return value

    @field_validator("payment_batch_id")
    @classmethod
    def validate_payment_batch_id(cls, value: str) -> str:
        if value is None:
            raise ValueError("payment_batch_id is required")
        if not isinstance(value, str):
            raise ValueError("payment_batch_id must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("payment_batch_id cannot be empty")
        return value


class TimeEntryCreate(BaseModel):
    freelancer_id: int
    task_id: int
    hours: float
    description: str | None = None
    logged_at: str

    @field_validator("freelancer_id")
    @classmethod
    def validate_freelancer_id(cls, value: int) -> int:
        if value is None:
            raise ValueError("freelancer_id is required")
        if not isinstance(value, int):
            raise ValueError("freelancer_id must be an integer")
        if value <= 0:
            raise ValueError("freelancer_id must be positive")
        return value

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, value: int) -> int:
        if value is None:
            raise ValueError("task_id is required")
        if not isinstance(value, int):
            raise ValueError("task_id must be an integer")
        if value <= 0:
            raise ValueError("task_id must be positive")
        return value

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, value: float) -> float:
        if value is None:
            raise ValueError("hours is required")
        if not isinstance(value, (int, float)):
            raise ValueError("hours must be a number")
        if value <= 0:
            raise ValueError("hours must be positive")
        return float(value)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("description must be a string")
        return value.strip()

    @field_validator("logged_at")
    @classmethod
    def validate_logged_at(cls, value: str) -> str:
        if value is None:
            raise ValueError("logged_at is required")
        if not isinstance(value, str):
            raise ValueError("logged_at must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("logged_at cannot be empty")
        return value


@router.post("/freelancers", status_code=201)
def create_freelancer(session: SessionDep, payload: FreelancerCreate) -> Any:
    try:
        dt_now = datetime.utcnow().isoformat()
        fl = Freelancer(
            name=payload.name,
            email=payload.email,
            hourly_rate=payload.hourly_rate,
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(fl)
        session.commit()
        session.refresh(fl)
        return {
            "id": fl.id,
            "name": fl.name,
            "email": fl.email,
            "hourly_rate": fl.hourly_rate,
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/tasks", status_code=201)
def create_task(session: SessionDep, payload: TaskCreate) -> Any:
    try:
        dt_now = datetime.utcnow().isoformat()
        tsk = Task(
            name=payload.name,
            description=payload.description,
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(tsk)
        session.commit()
        session.refresh(tsk)
        return {"id": tsk.id, "name": tsk.name, "description": tsk.description}
    except Exception as e:
        return {"error": str(e)}


@router.post("/entries", status_code=201)
def create_time_entry(session: SessionDep, payload: TimeEntryCreate) -> Any:
    try:
        fl = session.exec(
            select(Freelancer).where(Freelancer.id == payload.freelancer_id)
        ).first()
        if not fl:
            raise HTTPException(status_code=404, detail="Freelancer not found")

        tsk = session.exec(select(Task).where(Task.id == payload.task_id)).first()
        if not tsk:
            raise HTTPException(status_code=404, detail="Task not found")

        dt_now = datetime.utcnow().isoformat()
        ent = TimeEntry(
            freelancer_id=payload.freelancer_id,
            task_id=payload.task_id,
            hours=payload.hours,
            description=payload.description,
            logged_at=payload.logged_at,
            created_at=dt_now,
            updated_at=dt_now,
        )
        session.add(ent)
        session.commit()
        session.refresh(ent)
        return {
            "id": ent.id,
            "freelancer_id": ent.freelancer_id,
            "task_id": ent.task_id,
            "hours": ent.hours,
            "description": ent.description,
            "logged_at": ent.logged_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.get("/")
def list_worklogs(
    session: SessionDep, dt_from: str | None = None, dt_to: str | None = None
) -> Any:
    try:
        tsks = session.exec(select(Task)).all()
        res = []

        for tsk in tsks:
            ents = session.exec(
                select(TimeEntry).where(TimeEntry.task_id == tsk.id)
            ).all()

            t_hrs = 0.0
            t_amt = 0.0
            filt_ents = []

            for ent in ents:
                if dt_from and ent.logged_at < dt_from:
                    continue
                if dt_to and ent.logged_at > dt_to:
                    continue

                filt_ents.append(ent)
                fl = session.exec(
                    select(Freelancer).where(Freelancer.id == ent.freelancer_id)
                ).first()
                if fl:
                    amt = ent.hours * fl.hourly_rate
                    t_hrs += ent.hours
                    t_amt += amt

            # Determine overall payment status for this task
            task_status = "unpaid"
            if filt_ents:
                paid_count = sum(1 for e in filt_ents if e.payment_status == "paid")
                if paid_count == len(filt_ents):
                    task_status = "paid"
                elif paid_count > 0:
                    task_status = "partial"

            res.append(
                {
                    "id": tsk.id,
                    "name": tsk.name,
                    "description": tsk.description,
                    "total_hours": t_hrs,
                    "total_amount": t_amt,
                    "entry_count": len(filt_ents),
                    "payment_status": task_status,
                }
            )

        return {"data": res, "count": len(res)}
    except Exception as e:
        return {"error": str(e)}


@router.get("/{task_id}")
def get_worklog_detail(session: SessionDep, task_id: int) -> Any:
    try:
        tsk = session.exec(select(Task).where(Task.id == task_id)).first()
        if not tsk:
            raise HTTPException(status_code=404, detail="Task not found")

        ents = session.exec(select(TimeEntry).where(TimeEntry.task_id == task_id)).all()

        ent_list = []
        t_hrs = 0.0
        t_amt = 0.0

        for ent in ents:
            fl = session.exec(
                select(Freelancer).where(Freelancer.id == ent.freelancer_id)
            ).first()
            fl_name = ""
            rt = 0.0
            amt = 0.0

            if fl:
                fl_name = fl.name
                rt = fl.hourly_rate
                amt = ent.hours * rt

            t_hrs += ent.hours
            t_amt += amt

            ent_list.append(
                {
                    "id": ent.id,
                    "freelancer_id": ent.freelancer_id,
                    "freelancer_name": fl_name,
                    "hours": ent.hours,
                    "hourly_rate": rt,
                    "amount": amt,
                    "description": ent.description,
                    "logged_at": ent.logged_at,
                    "created_at": ent.created_at,
                    "payment_status": ent.payment_status,
                    "paid_at": ent.paid_at,
                    "payment_batch_id": ent.payment_batch_id,
                }
            )

        return {
            "id": tsk.id,
            "name": tsk.name,
            "description": tsk.description,
            "total_hours": t_hrs,
            "total_amount": t_amt,
            "entries": ent_list,
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.post("/mark-paid")
def mark_paid(session: SessionDep, payload: MarkPaidRequest) -> Any:
    try:
        dt_now = datetime.utcnow().isoformat()
        cnt = 0

        for tsk_id in payload.task_ids:
            ents = session.exec(
                select(TimeEntry).where(
                    TimeEntry.task_id == tsk_id, TimeEntry.payment_status == "unpaid"
                )
            ).all()

            for ent in ents:
                ent.payment_status = "paid"
                ent.paid_at = dt_now
                ent.payment_batch_id = payload.payment_batch_id
                session.add(ent)
                cnt += 1

        session.commit()

        return {
            "success": True,
            "marked_paid": cnt,
            "payment_batch_id": payload.payment_batch_id,
        }
    except Exception as e:
        return {"error": str(e)}
