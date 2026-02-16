import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    PaymentBatchResponse,
    WorkLog,
    WorkLogCreate,
    WorkLogPublic,
    WorkLogsPublic,
    WorkLogUpdate,
    TimeEntry,
)


class WorkLogService:
    @staticmethod
    def get_worklogs(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> WorkLogsPublic:
        """
        Retrieve worklogs with optional date filtering on time entries.
        """
        # Fetch all worklogs - in a real app, we'd use DB-native JSON functions
        # for performance, but here we prioritize correctness across DB types.
        statement = select(WorkLog)
        all_wls = session.exec(statement).all()

        filtered_results = []
        for wl in all_wls:
            te_list = json.loads(wl.time_entries)
            entries = [TimeEntry(**e) for e in te_list]
            
            # Filtering logic: at least one entry must be within range
            matches = True
            if start_date or end_date:
                has_entry_in_range = False
                for entry in entries:
                    entry_date = entry.date # Expected to be YYYY-MM-DD
                    is_after_start = True
                    is_before_end = True
                    
                    if start_date:
                        is_after_start = entry_date >= start_date
                    if end_date:
                        is_before_end = entry_date <= end_date
                    
                    if is_after_start and is_before_end:
                        has_entry_in_range = True
                        break
                matches = has_entry_in_range

            if matches:
                filtered_results.append(
                    WorkLogPublic(
                        id=wl.id,
                        freelancer_id=wl.freelancer_id,
                        task_name=wl.task_name,
                        time_entries=entries,
                        total_hours=wl.total_hours,
                        hourly_rate=wl.hourly_rate,
                        total_earned=wl.total_earned,
                        status=wl.status,
                        created_at=wl.created_at,
                        updated_at=wl.updated_at,
                    )
                )

        # Apply pagination on the filtered result list
        total_count = len(filtered_results)
        paginated_data = filtered_results[skip : skip + limit]

        return WorkLogsPublic(data=paginated_data, count=total_count)

    @staticmethod
    def get_worklog(session: Session, wl_id: int) -> WorkLogPublic:
        """
        Get worklog by ID.
        """
        wl = session.get(WorkLog, wl_id)
        if not wl:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        te_list = json.loads(wl.time_entries)
        entries = [TimeEntry(**e) for e in te_list]
        return WorkLogPublic(
            id=wl.id,
            freelancer_id=wl.freelancer_id,
            task_name=wl.task_name,
            time_entries=entries,
            total_hours=wl.total_hours,
            hourly_rate=wl.hourly_rate,
            total_earned=wl.total_earned,
            status=wl.status,
            created_at=wl.created_at,
            updated_at=wl.updated_at,
        )

    @staticmethod
    def create_worklog(session: Session, wl_in: WorkLogCreate) -> WorkLogPublic:
        """
        Create new worklog.
        """
        te_list = [e.model_dump() for e in wl_in.time_entries]
        te_json = json.dumps(te_list)

        ttl_hrs = sum(e.hours for e in wl_in.time_entries)
        ttl_earned = ttl_hrs * wl_in.hourly_rate

        wl = WorkLog(
            freelancer_id=wl_in.freelancer_id,
            task_name=wl_in.task_name,
            time_entries=te_json,
            total_hours=ttl_hrs,
            hourly_rate=wl_in.hourly_rate,
            total_earned=ttl_earned,
            status="PENDING",
        )

        session.add(wl)
        session.commit()
        session.refresh(wl)

        return WorkLogService.get_worklog(session, wl.id)

    @staticmethod
    def update_worklog(
        session: Session, wl_id: int, wl_in: WorkLogUpdate
    ) -> WorkLogPublic:
        """
        Update a worklog.
        """
        wl = session.get(WorkLog, wl_id)
        if not wl:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        upd_dict = wl_in.model_dump(exclude_unset=True)

        if "time_entries" in upd_dict and upd_dict["time_entries"]:
            te_list = [e.model_dump() for e in upd_dict["time_entries"]]
            upd_dict["time_entries"] = json.dumps(te_list)
            upd_dict["total_hours"] = sum(e["hours"] for e in te_list)
            upd_dict["total_earned"] = upd_dict["total_hours"] * wl.hourly_rate

        if "hourly_rate" in upd_dict and upd_dict["hourly_rate"]:
            upd_dict["total_earned"] = wl.total_hours * upd_dict["hourly_rate"]

        upd_dict["updated_at"] = datetime.utcnow()

        wl.sqlmodel_update(upd_dict)
        session.add(wl)
        session.commit()
        session.refresh(wl)

        return WorkLogService.get_worklog(session, wl.id)

    @staticmethod
    def delete_worklog(session: Session, wl_id: int) -> dict:
        """
        Delete a worklog.
        """
        wl = session.get(WorkLog, wl_id)
        if not wl:
            raise HTTPException(status_code=404, detail="WorkLog not found")

        session.delete(wl)
        session.commit()
        return {"message": "WorkLog deleted successfully"}

    @staticmethod
    def process_payment_batch(
        session: Session, wl_ids: list[int]
    ) -> PaymentBatchResponse:
        """
        Process payment for selected worklogs.
        """
        processed = 0
        ttl_amt = 0.0

        for wl_id in wl_ids:
            wl = session.get(WorkLog, wl_id)
            if wl and wl.status == "PENDING":
                wl.status = "PAID"
                wl.updated_at = datetime.utcnow()
                session.add(wl)
                processed += 1
                ttl_amt += wl.total_earned

        session.commit()

        return PaymentBatchResponse(
            processed=processed, total=len(wl_ids), total_amount=ttl_amt
        )
