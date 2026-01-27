from sqlmodel import Session, select
from app.models import WorkLog, Remittance
from datetime import datetime


def run_settlement(session: Session, start: datetime, end: datetime):
    all_logs = session.exec(
        select(WorkLog)
        .where(WorkLog.start_time >= start)
        .where(WorkLog.end_time <= end)
    ).all()

    totals = {}
    for log in all_logs:
        hours = (log.end_time - log.start_time).total_seconds() / 3600
        totals.setdefault(log.user_id, 0)
        totals[log.user_id] += hours * 100

    results = []
    for user_id, amount in totals.items():
        rem = Remittance(
            user_id=user_id,
            amount=amount,
            period_start=start,
            period_end=end,
            status="REMITTED",
        )
        session.add(rem)
        session.flush()
        session.commit()
        session.refresh(rem)   # ← critical line
        results.append(rem)
        print(results, "results***************************************************************************************")

    return results


    print(results, "results***************************************************************************************")
    session.commit()
    return results
