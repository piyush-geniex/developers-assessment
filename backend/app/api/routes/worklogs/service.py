import uuid
from collections import defaultdict
from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlmodel import Session, select

from app.models import (
    GenerateRemittancesForAllUsersRequest,
    GenerateRemittancesForAllUsersResponse,
    GenerateRemittanceUserResult,
    Remittance,
    RemittanceLine,
    RemittanceStatus,
    SettlementRun,
    SettlementRunStatus,
    Worklog,
    WorklogAmountsPublic,
    WorklogEntry,
    WorklogRemittanceStatus,
    WorklogsAmountsPublic,
)


class WorklogsService:
    @staticmethod
    def generate_remittances_for_all_users(
        session: Session,
        payload: GenerateRemittancesForAllUsersRequest,
        idempotency_key_header: str | None,
        payout_mode: str | None,
    ) -> GenerateRemittancesForAllUsersResponse:
        run_key = WorklogsService._get_run_key(
            payload.idempotency_key, idempotency_key_header
        )

        run = session.exec(
            select(SettlementRun).where(SettlementRun.idempotency_key == run_key)
        ).first()
        if run:
            return WorklogsService._build_run_response(session, run)

        run = SettlementRun(
            idempotency_key=run_key,
            status=SettlementRunStatus.IN_PROGRESS,
            period_from=payload.from_date,
            period_to=payload.to_date,
            started_at=datetime.utcnow(),
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        rem_map = WorklogsService._build_period_remaining_map(
            session=session,
            from_date=payload.from_date,
            to_date=payload.to_date,
        )
        usr_map: dict[uuid.UUID, dict[int, Decimal]] = defaultdict(dict)
        for wl_id, data in rem_map.items():
            usr_id = data["user_id"]
            if usr_id is None:
                continue
            usr_map[usr_id][wl_id] = data["remaining"]

        out: list[GenerateRemittanceUserResult] = []
        for usr_id, wl_map in usr_map.items():
            out.append(
                WorklogsService._settle_user(
                    session,
                    run,
                    run_key,
                    usr_id,
                    wl_map,
                    payout_mode,
                )
            )

        run.status = WorklogsService._derive_run_status(out)
        run.finished_at = datetime.utcnow()
        run.meta_json = {
            "users_processed": len(out),
            "generated_at": datetime.utcnow().isoformat(),
        }
        session.add(run)
        session.commit()
        session.refresh(run)

        return WorklogsService._build_run_response(session, run)

    @staticmethod
    def list_all_worklogs(
        session: Session,
        remittance_status: str | None,
    ) -> WorklogsAmountsPublic:
        items = WorklogsService._build_worklog_rows(session)
        if remittance_status:
            items = [x for x in items if x.remittance_status == remittance_status]
        return WorklogsAmountsPublic(data=items, count=len(items))

    @staticmethod
    def _build_worklog_rows(session: Session) -> list[WorklogAmountsPublic]:
        rem_map = WorklogsService._build_lifetime_remaining_map(session=session)
        wl_list = session.exec(select(Worklog)).all()
        out: list[WorklogAmountsPublic] = []
        for wl in wl_list:
            data = rem_map.get(
                wl.id or 0,
                {
                    "gross": Decimal("0.00"),
                    "remitted": Decimal("0.00"),
                    "remaining": Decimal("0.00"),
                    "user_id": wl.user_id,
                },
            )
            sts = (
                WorklogRemittanceStatus.REMITTED
                if data["remaining"] == Decimal("0.00")
                else WorklogRemittanceStatus.UNREMITTED
            )
            out.append(
                WorklogAmountsPublic(
                    worklog_id=wl.id or 0,
                    user_id=wl.user_id,
                    task_ref=wl.task_ref,
                    gross_amount=WorklogsService._to_money(data["gross"]),
                    remitted_amount=WorklogsService._to_money(data["remitted"]),
                    unremitted_amount=WorklogsService._to_money(data["remaining"]),
                    remittance_status=sts,
                )
            )
        return out

    @staticmethod
    def _build_lifetime_remaining_map(
        session: Session,
    ) -> dict[int, dict[str, Any]]:
        wl_list = session.exec(select(Worklog)).all()
        wl_usr_map: dict[int, uuid.UUID] = {
            wl.id: wl.user_id for wl in wl_list if wl.id is not None
        }
        gross_map: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        ent_list = session.exec(select(WorklogEntry)).all()
        for ent in ent_list:
            gross_map[ent.worklog_id] += WorklogsService._to_money(ent.amount_signed)

        remitted_map: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        rem_ids = session.exec(
            select(Remittance.id).where(Remittance.status == RemittanceStatus.REMITTED)
        ).all()
        if rem_ids:
            lines = session.exec(
                select(RemittanceLine).where(RemittanceLine.remittance_id.in_(rem_ids))
            ).all()
            for ln in lines:
                remitted_map[ln.worklog_id] += WorklogsService._to_money(ln.amount)

        out: dict[int, dict[str, Any]] = {}
        for wl_id, gross in gross_map.items():
            remitted = remitted_map[wl_id]
            out[wl_id] = {
                "gross": WorklogsService._to_money(gross),
                "remitted": WorklogsService._to_money(remitted),
                "remaining": WorklogsService._to_money(gross - remitted),
                "user_id": wl_usr_map.get(wl_id),
            }

        for wl_id, usr_id in wl_usr_map.items():
            if wl_id not in out:
                out[wl_id] = {
                    "gross": Decimal("0.00"),
                    "remitted": WorklogsService._to_money(remitted_map[wl_id]),
                    "remaining": WorklogsService._to_money(
                        Decimal("0.00") - remitted_map[wl_id]
                    ),
                    "user_id": usr_id,
                }

        return out

    @staticmethod
    def _build_period_remaining_map(
        session: Session,
        from_date: date,
        to_date: date,
    ) -> dict[int, dict[str, Any]]:
        wl_list = session.exec(select(Worklog)).all()
        wl_usr_map: dict[int, uuid.UUID] = {
            wl.id: wl.user_id for wl in wl_list if wl.id is not None
        }
        gross_map: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        from_dt = datetime.combine(from_date, time.min)
        to_dt = datetime.combine(to_date, time.max)
        ent_list = session.exec(
            select(WorklogEntry).where(
                WorklogEntry.occurred_at >= from_dt, WorklogEntry.occurred_at <= to_dt
            )
        ).all()
        for ent in ent_list:
            gross_map[ent.worklog_id] += WorklogsService._to_money(ent.amount_signed)

        remitted_map: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        run_ids = session.exec(
            select(SettlementRun.id).where(
                SettlementRun.period_from == from_date,
                SettlementRun.period_to == to_date,
            )
        ).all()
        if run_ids:
            rem_ids = session.exec(
                select(Remittance.id).where(
                    Remittance.status == RemittanceStatus.REMITTED,
                    Remittance.run_id.in_(run_ids),
                )
            ).all()
            if rem_ids:
                lines = session.exec(
                    select(RemittanceLine).where(
                        RemittanceLine.remittance_id.in_(rem_ids)
                    )
                ).all()
                for ln in lines:
                    remitted_map[ln.worklog_id] += WorklogsService._to_money(ln.amount)

        out: dict[int, dict[str, Any]] = {}
        for wl_id, gross in gross_map.items():
            remitted = remitted_map[wl_id]
            out[wl_id] = {
                "gross": WorklogsService._to_money(gross),
                "remitted": WorklogsService._to_money(remitted),
                "remaining": WorklogsService._to_money(gross - remitted),
                "user_id": wl_usr_map.get(wl_id),
            }
        return out

    @staticmethod
    def _settle_user(
        session: Session,
        run: SettlementRun,
        run_key: str,
        usr_id: uuid.UUID,
        wl_map: dict[int, Decimal],
        payout_mode: str | None,
    ) -> GenerateRemittanceUserResult:
        total = Decimal("0.00")
        for amt in wl_map.values():
            total += WorklogsService._to_money(amt)
        total = WorklogsService._to_money(total)

        if total <= Decimal("0.00"):
            rem = Remittance(
                run_id=run.id or 0,
                user_id=usr_id,
                status=RemittanceStatus.SKIPPED_NEGATIVE,
                total_amount=total,
                currency="USD",
                idempotency_key=run_key,
                failure_reason="net_due_is_not_positive",
            )
            session.add(rem)
            session.commit()
            session.refresh(rem)
            return GenerateRemittanceUserResult(
                user_id=usr_id,
                remittance_id=rem.id or 0,
                status=rem.status,
                amount=total,
                message="Skipped due to non-positive balance",
            )

        try:
            rem = Remittance(
                run_id=run.id or 0,
                user_id=usr_id,
                status=RemittanceStatus.FAILED,
                total_amount=total,
                currency="USD",
                idempotency_key=run_key,
                failure_reason="payout_not_attempted",
            )
            session.add(rem)
            session.flush()

            payout_status = WorklogsService._attempt_payout(usr_id, total, payout_mode)
            if payout_status == RemittanceStatus.REMITTED:
                rem.status = RemittanceStatus.REMITTED
                rem.failure_reason = None
                for wl_id, amt in wl_map.items():
                    if amt == Decimal("0.00"):
                        continue
                    ln = RemittanceLine(
                        remittance_id=rem.id or 0,
                        worklog_id=wl_id,
                        amount=WorklogsService._to_money(amt),
                        snapshot_note="immutable_line_allocation",
                    )
                    session.add(ln)
                session.commit()
                return GenerateRemittanceUserResult(
                    user_id=usr_id,
                    remittance_id=rem.id or 0,
                    status=rem.status,
                    amount=total,
                    message="Remitted successfully",
                )

            rem.status = RemittanceStatus.CANCELLED
            rem.failure_reason = "payout_cancelled"
            session.add(rem)
            session.commit()
            return GenerateRemittanceUserResult(
                user_id=usr_id,
                remittance_id=rem.id or 0,
                status=rem.status,
                amount=total,
                message="Payout cancelled",
            )
        except Exception as exc:
            session.rollback()
            rem = Remittance(
                run_id=run.id or 0,
                user_id=usr_id,
                status=RemittanceStatus.FAILED,
                total_amount=total,
                currency="USD",
                idempotency_key=run_key,
                failure_reason=str(exc)[:255],
            )
            session.add(rem)
            rem.status = RemittanceStatus.FAILED
            session.commit()
            session.refresh(rem)
            return GenerateRemittanceUserResult(
                user_id=usr_id,
                remittance_id=rem.id or 0,
                status=rem.status,
                amount=total,
                message="Payout failed",
            )

    @staticmethod
    def _attempt_payout(
        _usr_id: uuid.UUID, _amt: Decimal, payout_mode: str | None
    ) -> str:
        if payout_mode == "fail":
            raise RuntimeError("simulated_payout_failure")
        if payout_mode == "cancel":
            return RemittanceStatus.CANCELLED
        return RemittanceStatus.REMITTED

    @staticmethod
    def _derive_run_status(out: list[GenerateRemittanceUserResult]) -> str:
        if not out:
            return SettlementRunStatus.COMPLETED
        has_fail = any(
            x.status in (RemittanceStatus.FAILED, RemittanceStatus.CANCELLED)
            for x in out
        )
        if has_fail:
            return SettlementRunStatus.PARTIAL_SUCCESS
        return SettlementRunStatus.COMPLETED

    @staticmethod
    def _build_run_response(
        session: Session, run: SettlementRun
    ) -> GenerateRemittancesForAllUsersResponse:
        rems = session.exec(select(Remittance).where(Remittance.run_id == run.id)).all()
        out = [
            GenerateRemittanceUserResult(
                user_id=x.user_id,
                remittance_id=x.id or 0,
                status=x.status,
                amount=WorklogsService._to_money(x.total_amount),
                message=x.failure_reason or "ok",
            )
            for x in rems
        ]
        remitted_count = len([x for x in rems if x.status == RemittanceStatus.REMITTED])
        failed_count = len([x for x in rems if x.status == RemittanceStatus.FAILED])
        cancelled_count = len(
            [x for x in rems if x.status == RemittanceStatus.CANCELLED]
        )
        skipped_negative_count = len(
            [x for x in rems if x.status == RemittanceStatus.SKIPPED_NEGATIVE]
        )
        return GenerateRemittancesForAllUsersResponse(
            run_id=run.id or 0,
            run_status=run.status,
            idempotency_key=run.idempotency_key,
            remitted_count=remitted_count,
            failed_count=failed_count,
            cancelled_count=cancelled_count,
            skipped_negative_count=skipped_negative_count,
            results=out,
        )

    @staticmethod
    def _to_money(v: Decimal | int | float) -> Decimal:
        return Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _get_run_key(body_key: str | None, header_key: str | None) -> str:
        if body_key:
            return body_key
        if header_key:
            return header_key
        return uuid.uuid4().hex
