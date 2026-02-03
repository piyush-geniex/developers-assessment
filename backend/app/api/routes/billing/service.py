from collections import defaultdict
from sqlmodel import Session, select, col
from app.models import (
    WorkLog, TimeSegment, Remittance,
    RemittanceItem, RemittanceStatus
)


def generate_remittances_for_all_users(session: Session):
    processed_segments_query = (
        select(RemittanceItem.time_segment_id)
        .join(Remittance)
        .where(Remittance.status != RemittanceStatus.FAILED)
    )

    unpaid_segments = session.exec(
        select(TimeSegment).where(col(TimeSegment.id).not_in(processed_segments_query))
    ).all()

    if not unpaid_segments:
        return []

    segments_by_user = defaultdict(list)
    for seg in unpaid_segments:
        segments_by_user[seg.work_log.user_id].append(seg)

    created_remittances = []

    for user_id, segments in segments_by_user.items():
        total_payout = 0.0
        remittance = Remittance(user_id=user_id, total_amount=0.0)
        session.add(remittance)
        session.flush()

        for seg in segments:
            segment_amount = (seg.minutes / 60.0) * seg.hourly_rate
            total_payout += segment_amount

            session.add(
                RemittanceItem(
                    remittance_id=remittance.id,
                    time_segment_id=seg.id,
                    amount_covered=segment_amount,
                )
            )

        remittance.total_amount = total_payout
        created_remittances.append(remittance)

    session.commit()
    return created_remittances


def list_worklogs_by_remittance_status(session: Session, remittance_status: str):
    settled_segment_ids = set(
        session.exec(
            select(RemittanceItem.time_segment_id)
            .join(Remittance)
            .where(Remittance.status != RemittanceStatus.FAILED)
        ).all()
    )

    worklogs = session.exec(select(WorkLog)).all()
    results = []

    for log in worklogs:
        total_amount = 0.0
        has_unsettled = False

        for seg in log.time_segments:
            seg_amount = (seg.minutes / 60.0) * seg.hourly_rate
            total_amount += seg_amount

            if seg.id not in settled_segment_ids:
                has_unsettled = True

        is_remitted = not has_unsettled

        if (
            remittance_status == "REMITTED" and is_remitted
        ) or (
            remittance_status == "UNREMITTED" and not is_remitted
        ):
            results.append(
                {
                    "id": log.id,
                    "title": log.title,
                    "user_id": log.user_id,
                    "total_amount": round(total_amount, 2),
                    "status": "REMITTED" if is_remitted else "UNREMITTED",
                }
            )

    return results
