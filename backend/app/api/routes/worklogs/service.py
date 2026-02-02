import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    WorkLog,
    TimeSegment,
    Adjustment,
    Remittance,
    RemittanceLineItem,
    User,
    RemittanceStatus,
    WorkLogPublic,
)


class WorkLogService:
    """Service for handling worklog operations and settlement calculations"""

    @staticmethod
    def calculate_worklog_totals(session: Session, worklog_id: uuid.UUID) -> dict[str, Decimal]:
        """
        Calculate all financial metrics for a worklog
        """
        worklog = session.get(WorkLog, worklog_id)
        if not worklog:
            return None

        # Calculate total hours
        total_hours = session.exec(
            select(func.sum(TimeSegment.hours)).where(TimeSegment.worklog_id == worklog_id)
        ).one() or Decimal("0")

        # Get user's hourly rate
        user = session.get(User, worklog.user_id)
        # Assuming User has hourly_rate field, otherwise default to 20
        hourly_rate = worklog.hourly_rate
        if not hourly_rate:
            hourly_rate = 20

        # Calculate base amount
        base_amount = total_hours * hourly_rate

        # Calculate adjustments
        adjustments_total = session.exec(
            select(func.sum(Adjustment.amount)).where(Adjustment.worklog_id == worklog_id)
        ).one() or Decimal("0")

        # Total amount
        total_amount = base_amount + float(adjustments_total)

        # Calculate paid amount (from PAID remittances only)
        paid_amount = session.exec(
            select(func.sum(RemittanceLineItem.amount))
                .join(Remittance)
                .where(
                RemittanceLineItem.worklog_id == worklog_id,
                Remittance.status == RemittanceStatus.PAID
            )
        ).one() or Decimal("0")

        # Pending amount
        pending_amount = total_amount - float(paid_amount)

        return {
            'total_hours': total_hours,
            'base_amount': base_amount,
            'adjustments': adjustments_total,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'pending_amount': pending_amount
        }

    @staticmethod
    def get_worklog_remittance_status(session: Session, worklog_id: uuid.UUID) -> str:
        """Determine remittance status for a worklog"""
        totals = WorkLogService.calculate_worklog_totals(session, worklog_id)

        if totals is None:
            return "UNKNOWN"

        paid = totals['paid_amount']
        total = totals['total_amount']

        if total == 0:
            return "UNREMITTED"

        if paid >= total:
            return "FULLY_REMITTED"
        elif paid > 0:
            return "PARTIALLY_REMITTED"
        else:
            return "UNREMITTED"

    @staticmethod
    def list_all_worklogs(
            session: Session,
            remittance_status_filter: str | None = None
    ) -> list[WorkLogPublic]:
        """List all worklogs with financial information"""
        worklogs = session.exec(select(WorkLog)).all()

        result = []
        for worklog in worklogs:
            totals = WorkLogService.calculate_worklog_totals(session, worklog.id)
            status = WorkLogService.get_worklog_remittance_status(session, worklog.id)

            # Apply filter
            if remittance_status_filter:
                if remittance_status_filter.upper() == "REMITTED":
                    if status not in ["FULLY_REMITTED", "PARTIALLY_REMITTED"]:
                        continue
                elif remittance_status_filter.upper() == "UNREMITTED":
                    if status != "UNREMITTED":
                        continue

            time_segments_count = session.exec(
                select(func.count()).select_from(TimeSegment).where(TimeSegment.worklog_id == worklog.id)
            ).one()

            worklog_public = WorkLogPublic(
                id=worklog.id,
                user_id=worklog.user_id,
                task_name=worklog.task_name,
                description=worklog.description,
                created_at=worklog.created_at,
                updated_at=worklog.updated_at,
                total_hours=totals['total_hours'],
                total_amount=totals['total_amount'],
                paid_amount=totals['paid_amount'],
                pending_amount=totals['pending_amount'],
                remittance_status=status,
                time_segments_count=time_segments_count,
                adjustments_total=totals['adjustments']
            )
            result.append(worklog_public)

        return result

    @staticmethod
    def calculate_user_pending_amount(session: Session, user_id: uuid.UUID) -> tuple[Decimal, list[dict]]:
        """Calculate total pending amount for a user"""
        worklogs = session.exec(select(WorkLog).where(WorkLog.user_id == user_id)).all()

        total_pending = float(Decimal("0"))
        worklog_details = []

        for worklog in worklogs:
            totals = WorkLogService.calculate_worklog_totals(session, worklog.id)
            pending = totals['pending_amount']

            if pending != 0:
                total_pending += pending
                worklog_details.append({
                    'worklog_id': worklog.id,
                    'task_name': worklog.task_name,
                    'pending_amount': pending,
                    'total_hours': totals['total_hours'],
                    'adjustments': totals['adjustments']
                })

        return total_pending, worklog_details

    @staticmethod
    def generate_remittance_for_user(
            session: Session,
            user_id: uuid.UUID,
            settlement_period: str | None = None
    ) -> Remittance | None:
        """Generate a remittance for a user"""
        if settlement_period is None:
            settlement_period = datetime.utcnow().strftime("%Y-%m")

        total_pending, worklog_details = WorkLogService.calculate_user_pending_amount(session, user_id)

        if total_pending == 0:
            return None

        # Create remittance
        remittance = Remittance(
            user_id=user_id,
            total_amount=total_pending,
            status=RemittanceStatus.PENDING,
            settlement_period=settlement_period
        )
        session.add(remittance)
        session.flush()

        # Create line items
        for detail in worklog_details:
            line_item = RemittanceLineItem(
                remittance_id=remittance.id,
                worklog_id=detail['worklog_id'],
                amount=detail['pending_amount'],
                description=f"Settlement for {detail['task_name']}"
            )
            session.add(line_item)

        session.commit()
        session.refresh(remittance)

        return remittance

    @staticmethod
    def generate_remittances_for_all_users(
            session: Session,
            settlement_period: str | None = None
    ) -> list[Remittance]:
        """Generate remittances for all users"""
        users = session.exec(select(User)).all()

        remittances = []
        for user in users:
            remittance = WorkLogService.generate_remittance_for_user(
                session,
                user.id,
                settlement_period
            )
            if remittance:
                remittances.append(remittance)

        return remittances

    @staticmethod
    def seed_data_into_db(
            session: Session
    ):
        try:
            # Get existing users (assuming users already exist)
            users = session.exec(select(User)).all()

            if len(users) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Need at least 2 users in the system. Create users first."
                )

            user1 = users[0]
            user2 = users[1] if len(users) > 1 else users[0]
            user3 = users[2] if len(users) > 2 else users[0]

            # Create WorkLogs
            wl1 = WorkLog(
                user_id=user1.id,
                task_name="Build Login Page",
                description="Frontend login implementation with validation",
                hourly_rate=25
            )
            wl2 = WorkLog(
                user_id=user1.id,
                task_name="API Integration",
                description="Connect frontend to backend REST API",
                hourly_rate=20
            )
            wl3 = WorkLog(
                user_id=user2.id,
                task_name="Database Design",
                description="Design schema for user management system",
                hourly_rate=30
            )
            wl4 = WorkLog(
                user_id=user2.id,
                task_name="Bug Fixes",
                description="Fix critical production bugs",
                hourly_rate=40
            )
            wl5 = WorkLog(
                user_id=user3.id,
                task_name="Documentation",
                description="Write comprehensive API documentation",
                hourly_rate=40
            )

            session.add_all([wl1, wl2, wl3, wl4, wl5])
            session.commit()
            session.refresh(wl1)
            session.refresh(wl2)
            session.refresh(wl3)
            session.refresh(wl4)
            session.refresh(wl5)

            # Add Time Segments
            time_segments = [
                # WorkLog 1 (Build Login Page)
                TimeSegment(worklog_id=wl1.id, hours=Decimal("4.5"), description="Initial setup and structure"),
                TimeSegment(worklog_id=wl1.id, hours=Decimal("3.0"), description="Styling and validation logic"),
                TimeSegment(worklog_id=wl1.id, hours=Decimal("2.5"), description="Testing and bug fixes"),

                # WorkLog 2 (API Integration)
                TimeSegment(worklog_id=wl2.id, hours=Decimal("5.0"), description="API endpoint integration"),
                TimeSegment(worklog_id=wl2.id, hours=Decimal("3.5"), description="Error handling and validation"),

                # WorkLog 3 (Database Design)
                TimeSegment(worklog_id=wl3.id, hours=Decimal("8.0"), description="Schema design and modeling"),
                TimeSegment(worklog_id=wl3.id, hours=Decimal("4.0"), description="Review and revisions"),

                # WorkLog 4 (Bug Fixes)
                TimeSegment(worklog_id=wl4.id, hours=Decimal("6.0"), description="Critical bug investigation"),
                TimeSegment(worklog_id=wl4.id, hours=Decimal("2.0"), description="Testing and verification"),

                # WorkLog 5 (Documentation)
                TimeSegment(worklog_id=wl5.id, hours=Decimal("10.0"), description="Writing documentation"),
                TimeSegment(worklog_id=wl5.id, hours=Decimal("5.0"), description="Examples and diagrams"),
            ]
            session.add_all(time_segments)
            session.commit()

            # Add Adjustments (bonuses and deductions)
            adjustments = [
                # Bonus for early completion on WorkLog 1
                Adjustment(
                    worklog_id=wl1.id,
                    amount=Decimal("50.00"),
                    reason="Bonus for completing ahead of schedule"
                ),
                # Deduction for quality issue on WorkLog 4
                Adjustment(
                    worklog_id=wl4.id,
                    amount=Decimal("-60.00"),
                    reason="Quality issue - rework required on bug fixes"
                ),
                # Another deduction example
                Adjustment(
                    worklog_id=wl3.id,
                    amount=Decimal("-30.00"),
                    reason="Minor corrections needed in database schema"
                ),
            ]
            session.add_all(adjustments)
            session.commit()

            # Create a historical PAID remittance (simulating past month)
            past_remittance = Remittance(
                user_id=user1.id,
                total_amount=Decimal("250.00"),
                status=RemittanceStatus.PAID,
                settlement_period="2024-01",
                created_at=datetime.utcnow() - timedelta(days=30),
                updated_at=datetime.utcnow() - timedelta(days=30)
            )
            session.add(past_remittance)
            session.commit()
            session.refresh(past_remittance)

            # Add line item for the paid remittance (partial payment for wl1)
            past_line_item = RemittanceLineItem(
                remittance_id=past_remittance.id,
                worklog_id=wl1.id,
                amount=Decimal("250.00"),
                description="Partial settlement for Build Login Page"
            )
            session.add(past_line_item)

            # Create a FAILED remittance (simulating failed payment)
            failed_remittance = Remittance(
                user_id=user3.id,
                total_amount=Decimal("300.00"),
                status=RemittanceStatus.FAILED,
                settlement_period="2024-01",
                created_at=datetime.utcnow() - timedelta(days=15),
                updated_at=datetime.utcnow() - timedelta(days=15)
            )
            session.add(failed_remittance)
            session.commit()
            session.refresh(failed_remittance)

            # Add line item for failed remittance
            failed_line_item = RemittanceLineItem(
                remittance_id=failed_remittance.id,
                worklog_id=wl5.id,
                amount=Decimal("300.00"),
                description="Settlement for Documentation (FAILED)"
            )
            session.add(failed_line_item)
            session.commit()

            return {"message": "Test data seeded successfully! Created 5 worklogs, "
                               "11 time segments, 3 adjustments, and 2 historical remittances. "
                               "Now test the endpoints!"}

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Error seeding data: {str(e)}")
