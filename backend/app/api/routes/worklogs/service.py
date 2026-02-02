from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
    GenerateRemittancesRequest,
    GenerateRemittancesResponse,
    Remittance,
    User,
    WorkLog,
    WorkLogAdjustment,
    WorkLogAdjustmentCreate,
    WorkLogCreate,
    WorkLogDelta,
    WorkLogSegment,
    WorkLogSegmentCreate,
    WorkLogSummary,
    WorkLogsPublic,
    UserRemittanceSummary,
)


class WorklogsService:
    @staticmethod
    def create_worklog(session: Session, body: WorkLogCreate) -> WorkLog:
        user = session.get(User, body.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        worklog = WorkLog(
            user_id=body.user_id,
            task_code=body.task_code,
            description=body.description,
        )
        session.add(worklog)
        session.commit()
        session.refresh(worklog)
        return worklog

    @staticmethod
    def create_worklog_segment(
        session: Session, body: WorkLogSegmentCreate
    ) -> WorkLogSegment:
        worklog = session.get(WorkLog, body.worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        segment = WorkLogSegment(
            worklog_id=body.worklog_id,
            work_date=body.work_date,
            hours=body.hours,
            hourly_rate=body.hourly_rate,
            is_questioned=body.is_questioned,
        )
        session.add(segment)
        session.commit()
        session.refresh(segment)
        return segment

    @staticmethod
    def create_worklog_adjustment(
        session: Session, body: WorkLogAdjustmentCreate
    ) -> WorkLogAdjustment:
        worklog = session.get(WorkLog, body.worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        if body.segment_id is not None:
            segment = session.get(WorkLogSegment, body.segment_id)
            if not segment:
                raise HTTPException(status_code=404, detail="Segment not found")
            if segment.worklog_id != body.worklog_id:
                raise HTTPException(
                    status_code=400,
                    detail="Segment does not belong to the specified WorkLog",
                )

        adjustment = WorkLogAdjustment(
            worklog_id=body.worklog_id,
            segment_id=body.segment_id,
            amount=body.amount,
            reason=body.reason,
            effective_date=body.effective_date,
        )
        session.add(adjustment)
        session.commit()
        session.refresh(adjustment)
        return adjustment

    @staticmethod
    def generate_remittances_for_all_users(
        session: Session, body: GenerateRemittancesRequest
    ) -> GenerateRemittancesResponse:
        if body.period_start > body.period_end:
            raise HTTPException(status_code=400, detail="period_start must be before period_end")

        worklogs = session.exec(select(WorkLog)).all()
        if not worklogs:
            return GenerateRemittancesResponse(remittances=[])

        remittances_by_user: dict[Any, UserRemittanceSummary] = {}
        segments_to_settle: list[WorkLogSegment] = []
        adjustments_to_settle: list[WorkLogAdjustment] = []

        for wl in worklogs:
            unsettled_segments = [
                s
                for s in wl.segments
                if (not s.is_settled)
                and (not s.is_questioned)
                and (s.work_date <= body.period_end)
            ]
            unsettled_adjustments = [
                a
                for a in wl.adjustments
                if (not a.is_settled) and (a.effective_date <= body.period_end)
            ]

            if not unsettled_segments and not unsettled_adjustments:
                continue

            seg_total = sum((s.hours * s.hourly_rate for s in unsettled_segments), Decimal("0"))
            adj_total = sum((a.amount for a in unsettled_adjustments), Decimal("0"))
            delta = seg_total + adj_total

            if delta == 0:
                continue

            segments_to_settle.extend(unsettled_segments)
            adjustments_to_settle.extend(unsettled_adjustments)

            user_id = wl.user_id
            if user_id not in remittances_by_user:
                remittances_by_user[user_id] = UserRemittanceSummary(
                    user_id=user_id,
                    period_start=body.period_start,
                    period_end=body.period_end,
                    total_amount=Decimal("0"),
                    status="SUCCESS",
                    worklogs=[],
                )

            summary = remittances_by_user[user_id]
            summary.total_amount += delta
            summary.worklogs.append(WorkLogDelta(worklog_id=wl.id, delta_amount=delta))

        if not remittances_by_user:
            return GenerateRemittancesResponse(remittances=[])

        # Ensure users exist and create remittance records
        for user_id, summary in remittances_by_user.items():
            user = session.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found for remittance generation")

            if summary.total_amount == 0:
                continue

            remittance = Remittance(
                user_id=user_id,
                period_start=summary.period_start,
                period_end=summary.period_end,
                total_amount=summary.total_amount,
                status=summary.status,
            )
            session.add(remittance)

        for seg in segments_to_settle:
            seg.is_settled = True
            session.add(seg)

        for adj in adjustments_to_settle:
            adj.is_settled = True
            session.add(adj)

        session.commit()

        return GenerateRemittancesResponse(remittances=list(remittances_by_user.values()))

    @staticmethod
    def list_all_worklogs(
        session: Session, remittance_status: str | None
    ) -> WorkLogsPublic:
        allowed_status = {"REMITTED", "UNREMITTED"}
        if remittance_status is not None and remittance_status not in allowed_status:
            raise HTTPException(status_code=400, detail="Invalid remittanceStatus value")

        worklogs = session.exec(select(WorkLog)).all()
        summaries: list[WorkLogSummary] = []

        for wl in worklogs:
            seg_total = sum(
                (
                    s.hours * s.hourly_rate
                    for s in wl.segments
                    if not s.is_questioned
                ),
                Decimal("0"),
            )
            adj_total = sum((a.amount for a in wl.adjustments), Decimal("0"))
            total_amount = seg_total + adj_total

            has_unsettled = any(not s.is_settled for s in wl.segments) or any(
                not a.is_settled for a in wl.adjustments
            )

            status = "UNREMITTED" if has_unsettled else "REMITTED"

            if remittance_status is not None and status != remittance_status:
                continue

            summaries.append(
                WorkLogSummary(
                    worklog_id=wl.id,
                    user_id=wl.user_id,
                    total_amount=total_amount,
                    remittance_status=status,
                )
            )

        return WorkLogsPublic(data=summaries, count=len(summaries))
