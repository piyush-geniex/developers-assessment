from datetime import date, datetime

from pydantic import BaseModel, field_validator


class FreelancerResponse(BaseModel):
    """Response model for freelancer."""

    id: int
    name: str
    email: str
    hourly_rate: float
    created_at: datetime


class FreelancerListResponse(BaseModel):
    """Response model for list of freelancers."""

    data: list[FreelancerResponse]
    count: int


class TimeEntryResponse(BaseModel):
    """Response model for a time entry."""

    id: int
    start_time: datetime | None
    end_time: datetime | None
    hours: float | None
    created_at: datetime


class WorkLogListItem(BaseModel):
    """Response model for worklog in list view."""

    id: int
    task_name: str | None
    description: str | None
    freelancer_id: int | None
    freelancer_name: str | None
    freelancer_email: str | None
    hourly_rate: float | None
    total_hours: float
    earned_amount: float
    status: str | None
    payment_id: int | None
    created_at: datetime


class WorkLogListResponse(BaseModel):
    """Response model for list of worklogs."""

    data: list[WorkLogListItem]
    count: int


class WorkLogDetailResponse(BaseModel):
    """Response model for worklog detail with time entries."""

    id: int
    task_name: str | None
    description: str | None
    freelancer_id: int | None
    freelancer_name: str | None
    freelancer_email: str | None
    hourly_rate: float | None
    total_hours: float
    earned_amount: float
    status: str | None
    payment_id: int | None
    created_at: datetime
    time_entries: list[TimeEntryResponse]


class PaymentCreate(BaseModel):
    """Request model for creating a payment batch."""

    date_range_start: date
    date_range_end: date
    excluded_wl_ids: list[int] = []
    excluded_freelancer_ids: list[int] = []

    @field_validator("date_range_start")
    @classmethod
    def validate_date_range_start(cls, value: date) -> date:
        """
        value: start date for payment range
        """
        if value is None:
            raise ValueError("date_range_start is required")

        if not isinstance(value, date):
            raise ValueError("date_range_start must be a date")

        return value

    @field_validator("date_range_end")
    @classmethod
    def validate_date_range_end(cls, value: date) -> date:
        """
        value: end date for payment range
        """
        if value is None:
            raise ValueError("date_range_end is required")

        if not isinstance(value, date):
            raise ValueError("date_range_end must be a date")

        return value

    @field_validator("excluded_wl_ids")
    @classmethod
    def validate_excluded_wl_ids(cls, value: list[int]) -> list[int]:
        """
        value: list of worklog IDs to exclude
        """
        if not isinstance(value, list):
            raise ValueError("excluded_wl_ids must be a list")

        for wl_id in value:
            if not isinstance(wl_id, int):
                raise ValueError("each excluded worklog ID must be an integer")

        return value

    @field_validator("excluded_freelancer_ids")
    @classmethod
    def validate_excluded_freelancer_ids(cls, value: list[int]) -> list[int]:
        """
        value: list of freelancer IDs to exclude
        """
        if not isinstance(value, list):
            raise ValueError("excluded_freelancer_ids must be a list")

        for f_id in value:
            if not isinstance(f_id, int):
                raise ValueError("each excluded freelancer ID must be an integer")

        return value


class PaymentWorkLogItem(BaseModel):
    """Worklog item within a payment response."""

    id: int
    task_name: str | None
    freelancer_name: str | None
    freelancer_id: int | None
    total_hours: float
    earned_amount: float


class PaymentResponse(BaseModel):
    """Response model for a payment batch."""

    id: int
    status: str
    total_amount: float
    date_range_start: date
    date_range_end: date
    created_at: datetime
    worklogs: list[PaymentWorkLogItem]


class PaymentListItem(BaseModel):
    """Response model for payment in list view."""

    id: int
    status: str
    total_amount: float
    date_range_start: date
    date_range_end: date
    created_at: datetime
    wl_count: int


class PaymentListResponse(BaseModel):
    """Response model for list of payments."""

    data: list[PaymentListItem]
    count: int
