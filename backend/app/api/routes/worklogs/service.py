import uuid
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
	Remittance,
	WorkLog,
	WorkLogAdjustment,
	WorkLogSegment,
)


class WorkLogRemittanceStatus:
	REMITTED = "REMITTED"
	UNREMITTED = "UNREMITTED"


class SettlementService:
	@staticmethod
	def _calculate_worklog_current_amount(session: Session, worklog: WorkLog) -> Decimal:
		segments = session.exec(
			select(WorkLogSegment).where(
				WorkLogSegment.worklog_id == worklog.id,
				WorkLogSegment.is_active.is_(True),
			)
		).all()

		total_from_segments = Decimal("0.00")
		for segment in segments:
			duration = segment.end_time - segment.start_time
			hours = Decimal(duration.total_seconds()) / Decimal(3600)
			if hours < 0:
				raise HTTPException(status_code=400, detail="Segment has negative duration")
			total_from_segments += (segment.hourly_rate * hours).quantize(Decimal("0.01"))

		adjustments = session.exec(
			select(WorkLogAdjustment).where(WorkLogAdjustment.worklog_id == worklog.id)
		).all()
		total_adjustments = sum((adj.amount for adj in adjustments), start=Decimal("0.00"))

		return (total_from_segments + total_adjustments).quantize(Decimal("0.01"))

	@staticmethod
	def _get_worklog_status(current_amount: Decimal, remitted_amount: Decimal) -> str:
		if current_amount > Decimal("0.00") and current_amount == remitted_amount:
			return WorkLogRemittanceStatus.REMITTED
		return WorkLogRemittanceStatus.UNREMITTED

	@staticmethod
	def list_all_worklogs(
		session: Session,
		remittance_status: str | None = None,
	) -> dict[str, Any]:
		worklogs = session.exec(select(WorkLog)).all()

		data: list[dict[str, Any]] = []
		for worklog in worklogs:
			current_amount = SettlementService._calculate_worklog_current_amount(session, worklog)
			status = SettlementService._get_worklog_status(current_amount, worklog.total_remitted_amount)

			if remittance_status and status != remittance_status:
				continue

			data.append(
				{
					"id": worklog.id,
					"user_id": worklog.user_id,
					"task_name": worklog.task_name,
					"description": worklog.description,
					"amount": float(current_amount),
					"remittance_status": status,
				}
			)

		return {"data": data, "count": len(data)}

	@staticmethod
	def generate_remittances_for_all_users(
		session: Session,
		period_start: date | None = None,
		period_end: date | None = None,
	) -> dict[str, Any]:
		worklogs = session.exec(select(WorkLog)).all()

		deltas_by_user: dict[uuid.UUID, Decimal] = defaultdict(lambda: Decimal("0.00"))
		worklogs_by_user: dict[uuid.UUID, list[tuple[WorkLog, Decimal]]] = defaultdict(list)

		for worklog in worklogs:
			current_amount = SettlementService._calculate_worklog_current_amount(session, worklog)
			delta = (current_amount - worklog.total_remitted_amount).quantize(Decimal("0.01"))

			if delta == Decimal("0.00"):
				continue

			deltas_by_user[worklog.user_id] += delta
			worklogs_by_user[worklog.user_id].append((worklog, delta))

		remittances: list[dict[str, Any]] = []
		now = datetime.utcnow()

		for user_id, total_delta in deltas_by_user.items():
			if total_delta == Decimal("0.00"):
				continue

			remittance = Remittance(
				user_id=user_id,
				period_start=period_start,
				period_end=period_end,
				created_at=now,
				amount=total_delta,
				status="SUCCEEDED",
			)
			session.add(remittance)

			for worklog, delta in worklogs_by_user[user_id]:
				worklog.total_remitted_amount = (
					worklog.total_remitted_amount + delta
				).quantize(Decimal("0.01"))
				session.add(worklog)

			session.flush()
			session.refresh(remittance)

			remittances.append(
				{
					"id": remittance.id,
					"user_id": remittance.user_id,
					"amount": float(remittance.amount),
					"status": remittance.status,
					"period_start": remittance.period_start,
					"period_end": remittance.period_end,
					"created_at": remittance.created_at,
				}
			)

		session.commit()

		return {"data": remittances, "count": len(remittances)}
