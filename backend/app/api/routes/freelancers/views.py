import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.freelancers.service import FreelancerService
from app.models import (
    FreelancerCreate,
    FreelancerPublic,
    FreelancersPublic,
    FreelancerUpdate,
    Message,
)

router = APIRouter(prefix="/freelancers", tags=["freelancers"])


@router.get("/", response_model=FreelancersPublic)
def read_freelancers(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
) -> Any:
    """
    Retrieve all freelancers.
    """
    return FreelancerService.get_freelancers(session, skip, limit, is_active)


@router.get("/{freelancer_id}", response_model=FreelancerPublic)
def read_freelancer(
    session: SessionDep,
    current_user: CurrentUser,
    freelancer_id: uuid.UUID,
) -> Any:
    """
    Get a freelancer by ID.
    """
    return FreelancerService.get_freelancer(session, freelancer_id)


@router.post("/", response_model=FreelancerPublic)
def create_freelancer(
    session: SessionDep,
    current_user: CurrentUser,
    freelancer_in: FreelancerCreate,
) -> Any:
    """
    Create a new freelancer.
    """
    return FreelancerService.create_freelancer(session, freelancer_in)


@router.patch("/{freelancer_id}", response_model=FreelancerPublic)
def update_freelancer(
    session: SessionDep,
    current_user: CurrentUser,
    freelancer_id: uuid.UUID,
    freelancer_in: FreelancerUpdate,
) -> Any:
    """
    Update a freelancer.
    """
    return FreelancerService.update_freelancer(session, freelancer_id, freelancer_in)


@router.delete("/{freelancer_id}")
def delete_freelancer(
    session: SessionDep,
    current_user: CurrentUser,
    freelancer_id: uuid.UUID,
) -> Message:
    """
    Delete a freelancer.
    """
    FreelancerService.delete_freelancer(session, freelancer_id)
    return Message(message="Freelancer deleted successfully")
