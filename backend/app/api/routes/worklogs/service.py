import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import Freelancer, TimeSegment, WorkLog


class WorkLogService:
    @staticmethod
    def calc_wl_amt(session: Session, wl_id: uuid.UUID) -> float:
        """
        Calculate worklog amount
        wl_id: worklog id
        Returns: total amount earned
        """
        try:
            wl = session.get(WorkLog, wl_id)
            if not wl:
                return 0.0

            fr = session.get(Freelancer, wl.freelancer_id)
            if not fr:
                return 0.0

            segs = session.exec(
                select(TimeSegment).where(TimeSegment.worklog_id == wl_id)
            ).all()

            ttl_hrs = sum(s.hours for s in segs)
            amt = ttl_hrs * fr.hourly_rate

            return amt
        except Exception:
            return 0.0

    @staticmethod
    def calc_ttl_hrs(session: Session, wl_id: uuid.UUID) -> float:
        """
        Calculate total hours for worklog
        wl_id: worklog id
        Returns: total hours
        """
        try:
            segs = session.exec(
                select(TimeSegment).where(TimeSegment.worklog_id == wl_id)
            ).all()
            return sum(s.hours for s in segs)
        except Exception:
            return 0.0

    @staticmethod
    def proc_pay_batch(session: Session, wl_ids: list[uuid.UUID]) -> dict:
        """
        Process payment batch
        wl_ids: worklog ids
        Returns: dict with processed count
        """
        processed = 0
        for wl_id in wl_ids:
            try:
                wl = session.get(WorkLog, wl_id)
                if wl and wl.payment_status == "UNPAID":
                    wl.payment_status = "PAID"
                    wl.paid_at = datetime.utcnow()
                    session.add(wl)
                    session.commit()
                    processed += 1
            except Exception:
                continue

        return {"processed": processed, "total": len(wl_ids)}
