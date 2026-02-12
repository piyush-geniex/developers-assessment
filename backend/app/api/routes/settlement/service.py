import logging
from datetime import datetime

from sqlmodel import Session, select

from app.models import (
    Adjustment,
    Remittance,
    RemittanceWorklog,
    TimeSegment,
    WorkLog,
)

logger = logging.getLogger(__name__)


class SettlementService:
    @staticmethod
    def calc_wl_amount(session: Session, wl_id: object) -> float:
        """
        Calculate worklog amount from active segments and adjustments.
        wl_id: worklog id
        Returns: total amount (segments + adjustments)
        """
        # Sum active segments: hours * rate
        segs = session.exec(
            select(TimeSegment).where(
                TimeSegment.worklog_id == wl_id,
                TimeSegment.status == "ACTIVE",
            )
        ).all()

        t = 0.0
        for s in segs:
            t += s.hours * s.rate

        # Sum active adjustments
        adjs = session.exec(
            select(Adjustment).where(
                Adjustment.worklog_id == wl_id,
                Adjustment.status == "ACTIVE",
            )
        ).all()

        for a in adjs:
            t += a.amount

        return round(t, 2)

    @staticmethod
    def calc_settled_amount(session: Session, wl_id: object) -> float:
        """
        Calculate how much has already been settled for a worklog.
        wl_id: worklog id
        Returns: total settled amount from SETTLED remittances
        """
        rw_entries = session.exec(
            select(RemittanceWorklog).where(
                RemittanceWorklog.worklog_id == wl_id,
            )
        ).all()

        t = 0.0
        for rw in rw_entries:
            rmtnc = session.get(Remittance, rw.remittance_id)
            if rmtnc and rmtnc.status == "SETTLED":
                t += rw.amount

        return round(t, 2)

    @staticmethod
    def get_remittance_status(session: Session, wl_id: object) -> str:
        """
        Determine if a worklog is REMITTED or UNREMITTED.
        wl_id: worklog id
        """
        wl_amt = SettlementService.calc_wl_amount(session, wl_id)
        settled = SettlementService.calc_settled_amount(session, wl_id)

        if wl_amt <= 0:
            return "UNREMITTED"

        if settled >= wl_amt:
            return "REMITTED"

        return "UNREMITTED"

    @staticmethod
    def generate_remittances(session: Session) -> dict:
        """
        Generate remittances for all users based on eligible work.
        For each user, computes remaining unsettled amounts across all worklogs,
        then creates a single PENDING remittance if there is a positive balance.
        Returns: dict with data (list of remittances) and count
        """
        period = datetime.utcnow().strftime("%Y-%m")

        # Get all unique user_ids from worklogs
        wls = session.exec(select(WorkLog)).all()
        usr_ids = list({wl.user_id for wl in wls})

        results = []
        for u_id in usr_ids:
            try:
                u_wls = [wl for wl in wls if wl.user_id == u_id]
                total_remaining = 0.0
                wl_contributions = []

                for wl in u_wls:
                    wl_amt = SettlementService.calc_wl_amount(session, wl.id)
                    settled = SettlementService.calc_settled_amount(session, wl.id)

                    # Also account for PENDING remittances to avoid duplicates
                    pending_rws = session.exec(
                        select(RemittanceWorklog).where(
                            RemittanceWorklog.worklog_id == wl.id,
                        )
                    ).all()
                    pending_amt = 0.0
                    for rw in pending_rws:
                        rmtnc = session.get(Remittance, rw.remittance_id)
                        if rmtnc and rmtnc.status == "PENDING":
                            pending_amt += rw.amount

                    remaining = wl_amt - settled - pending_amt

                    if remaining > 0:
                        wl_contributions.append(
                            {"wl_id": wl.id, "amt": round(remaining, 2)}
                        )
                        total_remaining += remaining

                total_remaining = round(total_remaining, 2)

                if total_remaining > 0:
                    rmtnc = Remittance(
                        user_id=u_id,
                        amount=total_remaining,
                        status="PENDING",
                        period=period,
                    )
                    session.add(rmtnc)
                    session.commit()
                    session.refresh(rmtnc)

                    # Link worklogs to this remittance
                    for contrib in wl_contributions:
                        rw = RemittanceWorklog(
                            remittance_id=rmtnc.id,
                            worklog_id=contrib["wl_id"],
                            amount=contrib["amt"],
                        )
                        session.add(rw)
                        session.commit()

                    results.append(rmtnc)

            except Exception as e:
                logging.error(f"Failed to generate remittance for user {u_id}: {e}")
                continue  # Don't let one failure stop the batch

        return {"data": results, "count": len(results)}

    @staticmethod
    def list_worklogs(
        session: Session,
        u_id: object | None,
        is_superuser: bool,
        status_filter: str | None,
    ) -> dict:
        """
        List all worklogs with amount and remittance status.
        u_id: user id (used to scope results for non-superusers)
        is_superuser: if True, return all worklogs
        status_filter: REMITTED or UNREMITTED
        Returns: dict with data (list of worklog items) and count
        """
        if is_superuser:
            wls = session.exec(select(WorkLog)).all()
        else:
            wls = session.exec(select(WorkLog).where(WorkLog.user_id == u_id)).all()

        results = []
        for wl in wls:
            try:
                wl_amt = SettlementService.calc_wl_amount(session, wl.id)
                rmtnc_status = SettlementService.get_remittance_status(session, wl.id)

                if status_filter and rmtnc_status != status_filter.upper():
                    continue

                results.append(
                    {
                        "id": wl.id,
                        "user_id": wl.user_id,
                        "title": wl.title,
                        "amount": round(wl_amt, 2),
                        "remittance_status": rmtnc_status,
                    }
                )
            except Exception as e:
                logging.error(f"Failed to process worklog {wl.id}: {e}")
                continue

        return {"data": results, "count": len(results)}
