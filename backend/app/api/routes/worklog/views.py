from fastapi import APIRouter, Query, status, HTTPException
from app.schemas import (
    RemittanceStatus,
    TaskCreateIn,
    TaskCreateOut,
    WorkLogCreateIn,
    WorkLogCreateOut,
)
from typing import Optional
from datetime import date, timedelta
from app.schemas import TaskCreateIn, TaskCreateOut, WorkLogCreateIn, WorkLogCreateOut
from .service import WorklogService
from fastapi import APIRouter
from app.api.routes.worklog.service import WorklogService
from app.api.deps import SessionDep
from fastapi import status


router = APIRouter(prefix="/assessment_task", tags=["assessment"])


@router.post("/create-task", response_model=TaskCreateOut,
             status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreateIn,
    session: SessionDep,
):
    """
    Create a new task.
    """
    return WorklogService.create_task(session, task_in)


@router.post(
    "/create-worklog",
    response_model=WorkLogCreateOut,
    status_code=status.HTTP_201_CREATED
)
def create_worklog(
    worklog_in: WorkLogCreateIn,
    session: SessionDep
):
    """
    Create a new worklog for a user and task.
    """
    return WorklogService.create_worklog(session, worklog_in)


router = APIRouter(prefix="/assessment_task", tags=["assessment"])


@router.post(
    "/create-task",
    response_model=TaskCreateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task"
)
def create_task(
    task_in: TaskCreateIn,
    session: SessionDep,
):
    """
    Create a new task that workers can log time against.

    **Request Body:**
    - `title`: Task title (required)
    - `description`: Task description (optional)

    **Response:**
    - Returns the created task with its UUID
    """
    return WorklogService.create_task(session, task_in)


@router.post(
    "/create-worklog",
    response_model=WorkLogCreateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new worklog"
)
def create_worklog(
    worklog_in: WorkLogCreateIn,
    session: SessionDep
):
    """
    Create a new worklog for a user and task.

    Time segments and adjustments are added separately after worklog creation.

    **Request Body:**
    - `user_id`: UUID of the user
    - `task_id`: UUID of the task

    **Response:**
    - Returns the created worklog with its UUID

    **Errors:**
    - 404: User or Task not found
    """
    return WorklogService.create_worklog(session, worklog_in)


@router.get(
    "/list-all-worklogs",
    summary="List all worklogs with financial details"
)
def list_all_worklogs(
    session: SessionDep,
    remittanceStatus: RemittanceStatus = Query(
        description="Filter by remittance status: REMITTED, UNREMITTED",

    )
):
    """
    List all worklogs with complete financial breakdown.

    **Query Parameters:**
    - `remittanceStatus`: 
      - `ALL`: All worklogs (default)
      - `REMITTED`: Only fully paid worklogs (remaining_amount <= 0)
      - `UNREMITTED`: Only worklogs with remaining balance (remaining_amount > 0)

    **Response includes per worklog:**
    - `worklog_id`: UUID of the worklog
    - `user_id`: UUID of the user
    - `user_name`: Full name of the user
    - `task_id`: UUID of the task
    - `task_title`: Title of the task
    - `total_amount`: Total value (time segments + adjustments)
    - `remitted_amount`: Amount already paid or pending payment
    - `remaining_amount`: Amount still to be paid (can be negative if deductions applied)
    - `is_fully_remitted`: Boolean indicating if fully paid
    - `time_segments_count`: Number of time entries
    - `adjustments_count`: Number of adjustments (positive or negative)

    **Use Cases:**
    - Financial reconciliation
    - Identify unpaid work
    - Track payment history
    - Handle retroactive adjustments
    """
    # Validate and normalize status
    status_upper = remittanceStatus.upper()

    valid_statuses = ["ALL", "REMITTED", "UNREMITTED"]
    if status_upper not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid remittanceStatus '{remittanceStatus}'. Must be one of: {', '.join(valid_statuses)}"
        )

    return WorklogService.list_worklogs(session, status_upper)


@router.get(
    "/list-all-remittances",  # Fixed typo: remittences → remittances
    summary="List all remittances with details"
)
def list_all_remittances(session: SessionDep):
    """
    List all remittances (payment batches) with complete details.

    **Response includes per remittance:**
    - `remittance_id`: UUID of the remittance
    - `user_id`: UUID of the user being paid
    - `user_name`: Full name of the user
    - `total_amount`: Total amount in this remittance
    - `status`: Current status (PENDING, PAID, CANCELLED, FAILED)
    - `period_start`: Start date of the payment period
    - `period_end`: End date of the payment period
    - `created_at`: When the remittance was created
    - `worklogs`: Array of included worklogs with amounts
    - `worklog_count`: Number of worklogs in this remittance

    **Use Cases:**
    - Track payment history
    - Identify failed payments that need reprocessing
    - Audit financial records
    - Reconcile payments with accounting systems

    **Statuses Explained:**
    - `PENDING`: Payment initiated but not yet completed
    - `PAID`: Successfully paid to worker
    - `CANCELLED`: Payment cancelled before completion
    - `FAILED`: Payment attempt failed (worker not paid, can be retried)
    """
    return WorklogService.get_all_remittances(session)


@router.post(
    "/generate-remittances-for-all-users",
    summary="Generate monthly remittances (payment run)"
)
def generate_remittances_for_all_users(
    session: SessionDep,
    period_start: Optional[date] = Query(
        default=None,
        description="Start date of remittance period (defaults to first day of current month)"
    ),
    period_end: Optional[date] = Query(
        default=None,
        description="End date of remittance period (defaults to last day of current month)"
    )
):
    """
    Generate remittances for all users based on unremitted work.

    This endpoint performs the monthly settlement run, creating payment batches
    for all workers with eligible work.

    **Behavior:**
    1. Calculates remaining amount for each worklog (total - already remitted)
    2. Only includes worklogs with positive remaining amounts
    3. Groups worklogs by user
    4. Creates one PENDING remittance per user
    5. Skips users with no eligible work
    6. Handles partial remittances correctly (work already partially paid)

    **Query Parameters (Optional):**
    - `period_start`: Custom start date (default: first day of current month)
    - `period_end`: Custom end date (default: last day of current month)

    **Response:**
    - `message`: Success message
    - `remittances_created`: Number of remittances created
    - `total_amount`: Total amount across all remittances
    - `period_start`: Start date used
    - `period_end`: End date used

    **Use Cases:**
    - Monthly payment runs
    - Settling up after adjustments/deductions
    - Re-processing failed payments (only unpaid amounts included)
    - Handling retroactive work additions

    **Financial Correctness:**
    - Safe to run multiple times (won't double-pay)
    - Handles work added after previous payments
    - Handles adjustments applied to already-paid work
    - Excludes CANCELLED and FAILED remittances from calculations

    **Example Scenario:**
```
    Month 1: Worker logs 10 hours, generates $100 remittance → PAID
    Month 2: Worker adds 5 more hours to same worklog
            + Quality deduction of -$10 applied retroactively

    Running generate again:
    - Total worklog value: $150 (15 hours)
    - Already remitted: $100 (from Month 1)
    - Adjustment: -$10
    - New remittance: $40 (150 - 100 - 10)
```
    """
    # Calculate period dates if not provided
    today = date.today()

    if not period_start:
        period_start = date(today.year, today.month, 1)

    if not period_end:
        if today.month == 12:
            period_end = date(today.year, 12, 31)
        else:
            period_end = date(today.year, today.month +
                              1, 1) - timedelta(days=1)

    # Validate date range
    if period_start > period_end:
        raise HTTPException(
            status_code=400,
            detail="period_start must be before or equal to period_end"
        )

    # Generate remittances
    result = WorklogService.generate_remittances(
        session, period_start, period_end)

    return {
        "message": "Remittances generated successfully",
        **result
    }
