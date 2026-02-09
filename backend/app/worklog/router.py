from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from app.api.deps import SessionDep
from app.worklog.models import Freelancer, Payment, TimeEntry, WorkLog
from app.worklog.schemas import (
    FreelancerCreate,
    FreelancerResponse,
    PaymentCreate,
    PaymentResponse,
    TimeEntryCreate,
    TimeEntryResponse,
    WorkLogCreate,
    WorkLogResponse,
)

router = APIRouter()


@router.post("/freelancers", response_model=FreelancerResponse, status_code=201)
def create_freelancer(payload: FreelancerCreate, session: SessionDep):
    fl = Freelancer(
        name=payload.name, email=payload.email, rate_per_hour=payload.rate_per_hour
    )
    session.add(fl)
    session.commit()
    session.refresh(fl)
    return fl


@router.get("/freelancers", response_model=list[FreelancerResponse])
def get_freelancers(session: SessionDep):
    fls = session.exec(select(Freelancer)).all()
    return fls


@router.post("/worklogs", response_model=WorkLogResponse, status_code=201)
def create_worklog(payload: WorkLogCreate, session: SessionDep):
    fl = session.exec(
        select(Freelancer).where(Freelancer.id == payload.freelancer_id)
    ).first()
    if not fl:
        raise HTTPException(status_code=404, detail="Freelancer not found")

    wl = WorkLog(freelancer_id=payload.freelancer_id, task_name=payload.task_name)
    session.add(wl)
    session.commit()
    session.refresh(wl)
    return wl


@router.get("/worklogs", response_model=list)
def get_worklogs(
    session: SessionDep, 
    sd: str | None = None, 
    ed: str | None = None,
    f_id: int | None = None,
    st: str | None = None
):
    """
    sd: start date
    ed: end date
    f_id: freelancer id
    st: status
    """
    wls = session.exec(select(WorkLog)).all()

    res = []
    for wl in wls:
        if f_id and wl.freelancer_id != f_id:
            continue
        if st and wl.status != st:
            continue
            
        fl = session.exec(select(Freelancer).where(Freelancer.id == wl.freelancer_id)).first()
        tes = session.exec(select(TimeEntry).where(TimeEntry.worklog_id == wl.id)).all()

        t = 0.0
        for e in tes:
            t += e.amount

        wl.total_amount = t
        session.add(wl)
        session.commit()

        if sd and ed:
            try:
                s_d = datetime.fromisoformat(sd.replace("Z", "+00:00"))
                e_d = datetime.fromisoformat(ed.replace("Z", "+00:00"))
                if wl.created_at < s_d or wl.created_at > e_d:
                    continue
            except Exception:
                pass

        res.append(
            {
                "id": wl.id,
                "f_id": wl.freelancer_id,
                "f_nm": fl.name if fl else "",
                "t_nm": wl.task_name,
                "st": wl.status,
                "ttl": wl.total_amount,
                "c_at": wl.created_at.isoformat() + "Z",
                "u_at": wl.updated_at.isoformat() + "Z",
            }
        )

    return res


@router.get("/worklogs/{worklog_id}", response_model=dict)
def get_worklog_detail(worklog_id: int, session: SessionDep):
    wl = session.exec(select(WorkLog).where(WorkLog.id == worklog_id)).first()
    if not wl:
        raise HTTPException(status_code=404, detail="WorkLog not found")

    fl = session.exec(select(Freelancer).where(Freelancer.id == wl.freelancer_id)).first()
    tes = session.exec(select(TimeEntry).where(TimeEntry.worklog_id == wl.id)).all()

    e_l = []
    for e in tes:
        e_l.append(
            {
                "id": e.id,
                "wl_id": e.worklog_id,
                "desc": e.description,
                "h": e.hours,
                "r": e.rate,
                "amt": e.amount,
                "e_dt": e.entry_date.isoformat() + "Z",
                "c_at": e.created_at.isoformat() + "Z",
            }
        )

    return {
        "id": wl.id,
        "f_id": wl.freelancer_id,
        "f_nm": fl.name if fl else "",
        "t_nm": wl.task_name,
        "st": wl.status,
        "ttl": wl.total_amount,
        "c_at": wl.created_at.isoformat() + "Z",
        "u_at": wl.updated_at.isoformat() + "Z",
        "ents": e_l,
    }


@router.post("/time-entries", response_model=TimeEntryResponse, status_code=201)
def create_time_entry(payload: TimeEntryCreate, session: SessionDep):
    wl = session.exec(select(WorkLog).where(WorkLog.id == payload.worklog_id)).first()
    if not wl:
        raise HTTPException(status_code=404, detail="WorkLog not found")

    amt = payload.hours * payload.rate

    te = TimeEntry(
        worklog_id=payload.worklog_id,
        description=payload.description,
        hours=payload.hours,
        rate=payload.rate,
        amount=amt,
    )
    session.add(te)
    session.commit()
    session.refresh(te)

    tes = session.exec(select(TimeEntry).where(TimeEntry.worklog_id == wl.id)).all()
    t = 0.0
    for e in tes:
        t += e.amount

    wl.total_amount = t
    session.add(wl)
    session.commit()

    return te


@router.get("/time-entries", response_model=list[TimeEntryResponse])
def get_time_entries(session: SessionDep, worklog_id: int | None = None):
    if worklog_id:
        ents = session.exec(
            select(TimeEntry).where(TimeEntry.worklog_id == worklog_id)
        ).all()
    else:
        ents = session.exec(select(TimeEntry)).all()
    return ents


@router.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(payload: PaymentCreate, session: SessionDep):
    wl_ids = payload.worklog_ids
    wls = []
    for w_id in wl_ids:
        wl = session.exec(select(WorkLog).where(WorkLog.id == w_id)).first()
        if not wl:
            raise HTTPException(status_code=404, detail=f"WorkLog {w_id} not found")
        wls.append(wl)

    fl_pay = {}
    for wl in wls:
        if wl.freelancer_id not in fl_pay:
            fl_pay[wl.freelancer_id] = {"amt": 0.0, "w_ids": []}
        fl_pay[wl.freelancer_id]["amt"] += wl.total_amount
        fl_pay[wl.freelancer_id]["w_ids"].append(wl.id)

    pys = []
    for f_id, d in fl_pay.items():
        p = Payment(
            freelancer_id=f_id,
            total_amount=d["amt"],
            worklog_ids=",".join(map(str, d["w_ids"])),
            status="COMPLETED",
        )
        session.add(p)
        session.commit()
        session.refresh(p)
        pys.append(p)

        for w_id in d["w_ids"]:
            wl = session.exec(select(WorkLog).where(WorkLog.id == w_id)).first()
            if wl:
                wl.status = "PAID"
                session.add(wl)
                session.commit()

    return pys[0] if pys else None


@router.get("/payments", response_model=list[PaymentResponse])
def get_payments(session: SessionDep):
    pys = session.exec(select(Payment)).all()
    return pys
