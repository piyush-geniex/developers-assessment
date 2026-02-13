from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.worklog import models as worklog_models
from app.worklog import schemas as worklog_schemas


class WorkLogService:
    @staticmethod
    def calc_wl_amt(wl: worklog_models.WorkLog) -> float:
        segs = wl.time_segments
        seg_ttl = sum(s.hours * s.rate for s in segs)
        adj_ttl = sum(a.amount for a in wl.adjustments)
        return seg_ttl - adj_ttl

    @staticmethod
    def get_wls_by_rmt_status(
        session: Session, rmt_status: str | None = None
    ) -> list[tuple[worklog_models.WorkLog, float]]:
        stmt = select(worklog_models.WorkLog).options(
            selectinload(worklog_models.WorkLog.time_segments),
            selectinload(worklog_models.WorkLog.adjustments),
        )
        wls = session.exec(stmt).all()
        wls_with_amt = []
        for wl in wls:
            amt = WorkLogService.calc_wl_amt(wl)
            if rmt_status == "REMITTED":
                rmt = session.exec(
                    select(worklog_models.Remittance)
                    .where(worklog_models.Remittance.user_id == wl.user_id)
                    .where(worklog_models.Remittance.status == worklog_models.RemittanceStatus.SUCCESS)
                    .where(worklog_models.Remittance.period_start <= wl.created_at)
                    .where(worklog_models.Remittance.period_end >= wl.created_at)
                ).first()
                if rmt:
                    wls_with_amt.append((wl, amt))
            elif rmt_status == "UNREMITTED":
                rmt = session.exec(
                    select(worklog_models.Remittance)
                    .where(worklog_models.Remittance.user_id == wl.user_id)
                    .where(worklog_models.Remittance.status == worklog_models.RemittanceStatus.SUCCESS)
                    .where(worklog_models.Remittance.period_start <= wl.created_at)
                    .where(worklog_models.Remittance.period_end >= wl.created_at)
                ).first()
                if not rmt:
                    wls_with_amt.append((wl, amt))
            else:
                wls_with_amt.append((wl, amt))
        return wls_with_amt

    @staticmethod
    def gen_rmtncs_for_all_usr(session: Session) -> worklog_schemas.GenerateRemittancesResponse:
        from app.models import User

        usrs = session.exec(select(User)).all()
        rmtncs_created = 0
        ttl_amt = 0.0
        rmtncs_list = []

        now = datetime.utcnow()
        period_end = now
        period_start = now - timedelta(days=30)

        for usr in usrs:
            stmt = (
                select(worklog_models.WorkLog)
                .where(worklog_models.WorkLog.user_id == usr.id)
                .options(
                    selectinload(worklog_models.WorkLog.time_segments),
                    selectinload(worklog_models.WorkLog.adjustments),
                )
            )
            wls = session.exec(stmt).all()

            eligible_amt = 0.0
            for wl in wls:
                rmt = session.exec(
                    select(worklog_models.Remittance)
                    .where(worklog_models.Remittance.user_id == usr.id)
                    .where(worklog_models.Remittance.status == worklog_models.RemittanceStatus.SUCCESS)
                    .where(worklog_models.Remittance.period_start <= wl.created_at)
                    .where(worklog_models.Remittance.period_end >= wl.created_at)
                ).first()
                if not rmt:
                    amt = WorkLogService.calc_wl_amt(wl)
                    eligible_amt += amt

            if eligible_amt > 0:
                rmtnc = worklog_models.Remittance(
                    user_id=usr.id,
                    amount=eligible_amt,
                    status=worklog_models.RemittanceStatus.PENDING,
                    period_start=period_start,
                    period_end=period_end,
                )
                session.add(rmtnc)
                session.commit()
                session.refresh(rmtnc)
                rmtncs_created += 1
                ttl_amt += eligible_amt
                rmtncs_list.append(rmtnc)

        return worklog_schemas.GenerateRemittancesResponse(
            remittances_created=rmtncs_created,
            total_amount=ttl_amt,
            remittances=[
                worklog_schemas.RemittanceResponse(
                    id=r.id,
                    user_id=r.user_id,
                    amount=r.amount,
                    status=r.status.value,
                    period_start=r.period_start,
                    period_end=r.period_end,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
                for r in rmtncs_list
            ],
        )

