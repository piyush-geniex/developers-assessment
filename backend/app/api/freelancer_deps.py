"""
Dependencies for freelancer authentication.
Separate from admin user authentication to ensure token isolation.
"""
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.models import Freelancer, FreelancerTokenPayload

# Separate OAuth2 scheme for freelancers with different token URL
freelancer_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/freelancer/login"
)

FreelancerTokenDep = Annotated[str, Depends(freelancer_oauth2)]


def get_current_freelancer(session: SessionDep, token: FreelancerTokenDep) -> Freelancer:
    """
    Validate freelancer JWT token and return the authenticated freelancer.

    Security: Only accepts tokens with type="freelancer" claim.
    This prevents admin tokens from being used on freelancer routes.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = FreelancerTokenPayload(**payload)

        # Ensure this is a freelancer token, not an admin token
        if token_data.type != "freelancer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token type - freelancer token required",
            )
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    freelancer = session.get(Freelancer, token_data.sub)
    if not freelancer:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    if not freelancer.is_active:
        raise HTTPException(status_code=400, detail="Inactive freelancer")
    if not freelancer.hashed_password:
        raise HTTPException(
            status_code=400,
            detail="Freelancer account not activated - please set a password"
        )
    return freelancer


CurrentFreelancer = Annotated[Freelancer, Depends(get_current_freelancer)]
