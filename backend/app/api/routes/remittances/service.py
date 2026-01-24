import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

import anyio

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
    Adjustment,
    Remittance,
    RemittanceLine,
    RemittanceLineSource,
    RemittanceStatus,
    SettlementStatus,
    TimeSegment,
    TimeSegmentState,
    WorkLog,
)
from app.schemas.remittance import (
    RemittanceRunRequest,
    RemittanceRunResult,
    WorkLogAmount,
    WorkLogPublic,
    WorkLogWithAmount,
    WorkLogsPublic,
)


class RemittanceService:
    @staticmethod
    async def _run_sync(func, *args, **kwargs):  # type: ignore[explicit-any]
        return await anyio.to_thread.run_sync(func, *args, **kwargs)

    @staticmethod
    async def _resolve_period(body: RemittanceRunRequest) -> tuple[date, date]:
        today = date.today()
        default_start = today.replace(day=1)
        next_month = (default_start + timedelta(days=32)).replace(day=1)
        default_end = next_month - timedelta(days=1)
        period_start = body.period_start or default_start
        period_end = body.period_end or default_end
        if period_end < period_start:
            raise HTTPException(status_code=400, detail="period_end must be on or after period_start")
        return period_start, period_end

    @staticmethod
    async def _calculate_segment_amount(minutes: int, hourly_rate_cents: int) -> int:
        raw = Decimal(minutes) * Decimal(hourly_rate_cents) / Decimal(60)
        rounded = raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(rounded)

    @staticmethod
    async def generate_remittances_for_all_users(
        *, session: Session, body: RemittanceRunRequest
    ) -> RemittanceRunResult:
        period_start, period_end = await RemittanceService._resolve_period(body)

        eligible_segments = (
            await RemittanceService._run_sync(
                session.exec,
                select(TimeSegment).where(
                    TimeSegment.status == TimeSegmentState.RECORDED,
                    TimeSegment.settlement_status == SettlementStatus.UNREMITTED,
                ),
            )
        ).all()
        eligible_adjustments = (
            await RemittanceService._run_sync(
                session.exec,
                select(Adjustment).where(Adjustment.settlement_status == SettlementStatus.UNREMITTED),
            )
        ).all()

        entries_by_user: dict[uuid.UUID, list[tuple[str, object]]] = defaultdict(list)
        for seg in eligible_segments:
            entries_by_user[seg.user_id].append(("segment", seg))
        for adj in eligible_adjustments:
            entries_by_user[adj.user_id].append(("adjustment", adj))

        remittances: list[Remittance] = []
        attempted_users: list[uuid.UUID] = []

        for user_uuid, entries in entries_by_user.items():
            attempted_users.append(user_uuid)
            segment_total = sum(
                entry.amount_cents
                for kind, entry in entries
                if kind == "segment"
            )
            adjustment_total = sum(
                entry.amount_cents
                for kind, entry in entries
                if kind == "adjustment"
            )
            gross_amount = segment_total + sum(
                entry.amount_cents
                for kind, entry in entries
                if kind == "adjustment" and entry.amount_cents > 0
            )
            net_amount = segment_total + adjustment_total
            if gross_amount == 0 and net_amount == 0:
                continue
            payout_status = body.payout_status or RemittanceStatus.SUCCESS
            remittance = Remittance(
                user_id=user_uuid,
                period_start=period_start,
                period_end=period_end,
                status=payout_status,
                gross_amount_cents=gross_amount,
                net_amount_cents=net_amount,
                failure_reason=(
                    "Payout marked as failed" if payout_status in {RemittanceStatus.FAILED, RemittanceStatus.CANCELLED} else None
                ),
                finalized_at=datetime.utcnow(),
            )

            if body.dry_run:
                remittances.append(remittance)
                continue

            session.add(remittance)
            await RemittanceService._run_sync(session.flush)

            if payout_status == RemittanceStatus.SUCCESS:
                for kind, entry in entries:
                    if kind == "segment":
                        entry.settlement_status = SettlementStatus.REMITTED
                        entry.remittance_id = remittance.id
                        line = RemittanceLine(
                            remittance_id=remittance.id,
                            user_id=user_uuid,
                            worklog_id=entry.worklog_id,
                            source_id=entry.id,
                            source_type=RemittanceLineSource.TIME_SEGMENT,
                            amount_cents=entry.amount_cents,
                        )
                    else:
                        entry.settlement_status = SettlementStatus.REMITTED
                        entry.remittance_id = remittance.id
                        line = RemittanceLine(
                            remittance_id=remittance.id,
                            user_id=user_uuid,
                            worklog_id=entry.worklog_id,
                            source_id=entry.id,
                            source_type=RemittanceLineSource.ADJUSTMENT,
                            amount_cents=entry.amount_cents,
                        )
                    session.add(entry)
                    session.add(line)
            else:
                session.add(remittance)

            await RemittanceService._run_sync(session.commit)
            await RemittanceService._run_sync(session.refresh, remittance)
            remittances.append(remittance)

        return RemittanceRunResult(
            remittances=remittances,
            attempted_user_ids=attempted_users,
            dry_run=body.dry_run,
        )

    @staticmethod
    async def list_all_worklogs(
        *, session: Session, remittance_status: SettlementStatus | None
    ) -> WorkLogsPublic:
        worklogs = (await RemittanceService._run_sync(session.exec, select(WorkLog))).all()
        if not worklogs:
            return WorkLogsPublic(data=[], count=0)

        worklog_ids = [wl.id for wl in worklogs]

        segments = (
            await RemittanceService._run_sync(
                session.exec,
                select(TimeSegment).where(
                    TimeSegment.worklog_id.in_(worklog_ids),
                    TimeSegment.status == TimeSegmentState.RECORDED,
                ),
            )
        ).all()
        adjustments = (
            await RemittanceService._run_sync(
                session.exec,
                select(Adjustment).where(Adjustment.worklog_id.in_(worklog_ids)),
            )
        ).all()

        amounts: dict[uuid.UUID, WorkLogAmount] = {}
        for wl_id in worklog_ids:
            amounts[wl_id] = WorkLogAmount(
                worklog_id=wl_id, remitted_amount_cents=0, unremitted_amount_cents=0
            )

        def _bucket(target_settlement: SettlementStatus) -> str:
            return "remitted_amount_cents" if target_settlement == SettlementStatus.REMITTED else "unremitted_amount_cents"

        for seg in segments:
            bucket = _bucket(seg.settlement_status)
            current = getattr(amounts[seg.worklog_id], bucket)
            setattr(amounts[seg.worklog_id], bucket, current + seg.amount_cents)

        for adj in adjustments:
            bucket = _bucket(adj.settlement_status)
            current = getattr(amounts[adj.worklog_id], bucket)
            setattr(amounts[adj.worklog_id], bucket, current + adj.amount_cents)

        data: list[WorkLogWithAmount] = []
        for wl in worklogs:
            amount = amounts[wl.id]
            if remittance_status == SettlementStatus.UNREMITTED and amount.unremitted_amount_cents == 0:
                continue
            if remittance_status == SettlementStatus.REMITTED and (
                amount.unremitted_amount_cents > 0 or amount.remitted_amount_cents == 0
            ):
                continue
            data.append(
                WorkLogWithAmount(
                    worklog=WorkLogPublic.model_validate(wl),
                    amounts=amount,
                )
            )

        return WorkLogsPublic(data=data, count=len(data))
