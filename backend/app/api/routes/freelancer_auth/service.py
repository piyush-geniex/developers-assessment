"""Service layer for freelancer authentication."""
from datetime import timedelta

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.models import (
    Freelancer,
    FreelancerPublicMe,
    FreelancerRegister,
    FreelancerToken,
    FreelancerUpdateMe,
    FreelancerUpdatePassword,
)


class FreelancerAuthService:
    """Service for freelancer authentication operations."""

    @staticmethod
    def login(session: Session, form_data: OAuth2PasswordRequestForm) -> FreelancerToken:
        """
        Authenticate freelancer and return JWT token.

        Args:
            session: Database session
            form_data: OAuth2 form with username (email) and password

        Returns:
            FreelancerToken with access_token

        Raises:
            HTTPException: If credentials are invalid or freelancer is inactive
        """
        # Find freelancer by email
        freelancer = session.exec(
            select(Freelancer).where(Freelancer.email == form_data.username)
        ).first()

        if not freelancer:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        if not freelancer.hashed_password:
            raise HTTPException(
                status_code=400,
                detail="Account not activated - please contact support or register"
            )

        if not security.verify_password(form_data.password, freelancer.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        if not freelancer.is_active:
            raise HTTPException(status_code=400, detail="Inactive freelancer account")

        # Create token with freelancer type claim
        access_token = security.create_access_token(
            subject=str(freelancer.id),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            extra_claims={"type": "freelancer"},
        )

        return FreelancerToken(access_token=access_token)

    @staticmethod
    def register(session: Session, data: FreelancerRegister) -> FreelancerPublicMe:
        """
        Register a new freelancer account.

        Args:
            session: Database session
            data: Registration data

        Returns:
            Created freelancer public profile

        Raises:
            HTTPException: If email already exists
        """
        # Check for existing freelancer with same email
        existing = session.exec(
            select(Freelancer).where(Freelancer.email == data.email)
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="A freelancer with this email already exists"
            )

        # Create new freelancer with hashed password
        freelancer = Freelancer(
            name=data.name,
            email=data.email,
            hourly_rate=data.hourly_rate,
            hashed_password=security.get_password_hash(data.password),
        )

        session.add(freelancer)
        session.commit()
        session.refresh(freelancer)

        return FreelancerPublicMe.model_validate(freelancer)

    @staticmethod
    def get_me(freelancer: Freelancer) -> FreelancerPublicMe:
        """Get current freelancer's profile."""
        return FreelancerPublicMe.model_validate(freelancer)

    @staticmethod
    def update_me(
        session: Session,
        freelancer: Freelancer,
        data: FreelancerUpdateMe
    ) -> FreelancerPublicMe:
        """
        Update current freelancer's profile.

        Only allows updating name and hourly_rate.
        Email changes require verification (not implemented).
        """
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(freelancer, field, value)

        session.add(freelancer)
        session.commit()
        session.refresh(freelancer)

        return FreelancerPublicMe.model_validate(freelancer)

    @staticmethod
    def update_password(
        session: Session,
        freelancer: Freelancer,
        data: FreelancerUpdatePassword
    ) -> None:
        """
        Update freelancer's password.

        Args:
            session: Database session
            freelancer: Current authenticated freelancer
            data: Current and new password

        Raises:
            HTTPException: If current password is incorrect
        """
        if not freelancer.hashed_password:
            raise HTTPException(status_code=400, detail="No password set")

        if not security.verify_password(data.current_password, freelancer.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect current password")

        freelancer.hashed_password = security.get_password_hash(data.new_password)
        session.add(freelancer)
        session.commit()
