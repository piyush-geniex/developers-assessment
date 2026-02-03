"""API endpoints for freelancer authentication."""
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep
from app.api.freelancer_deps import CurrentFreelancer
from app.models import (
    FreelancerPublicMe,
    FreelancerRegister,
    FreelancerToken,
    FreelancerUpdateMe,
    FreelancerUpdatePassword,
    Message,
)

from .service import FreelancerAuthService

router = APIRouter(prefix="/freelancer", tags=["freelancer-auth"])


@router.post("/login", response_model=FreelancerToken)
def freelancer_login(
    session: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Freelancer login endpoint.

    Returns JWT access token for authenticated freelancer.
    Token includes type="freelancer" claim to distinguish from admin tokens.
    """
    return FreelancerAuthService.login(session, form_data)


@router.post("/register", response_model=FreelancerPublicMe)
def freelancer_register(
    session: SessionDep,
    data: FreelancerRegister,
) -> Any:
    """
    Register a new freelancer account.

    Creates a new freelancer with the provided details and password.
    Returns the created freelancer profile (without sensitive data).
    """
    return FreelancerAuthService.register(session, data)


@router.get("/me", response_model=FreelancerPublicMe)
def get_freelancer_me(
    current_freelancer: CurrentFreelancer,
) -> Any:
    """
    Get current freelancer's profile.

    Requires valid freelancer JWT token.
    """
    return FreelancerAuthService.get_me(current_freelancer)


@router.patch("/me", response_model=FreelancerPublicMe)
def update_freelancer_me(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    data: FreelancerUpdateMe,
) -> Any:
    """
    Update current freelancer's profile.

    Allows updating name and hourly_rate only.
    Requires valid freelancer JWT token.
    """
    return FreelancerAuthService.update_me(session, current_freelancer, data)


@router.post("/me/password", response_model=Message)
def update_freelancer_password(
    session: SessionDep,
    current_freelancer: CurrentFreelancer,
    data: FreelancerUpdatePassword,
) -> Any:
    """
    Update current freelancer's password.

    Requires current password for verification.
    """
    FreelancerAuthService.update_password(session, current_freelancer, data)
    return Message(message="Password updated successfully")
