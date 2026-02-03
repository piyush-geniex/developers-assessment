import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import (
    Freelancer,
    FreelancerCreate,
    FreelancerPublic,
    FreelancersPublic,
    FreelancerUpdate,
)


class FreelancerService:
    @staticmethod
    def get_freelancers(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> FreelancersPublic:
        """Retrieve all freelancers with optional filtering."""
        query = select(Freelancer)
        count_query = select(func.count()).select_from(Freelancer)

        if is_active is not None:
            query = query.where(Freelancer.is_active == is_active)
            count_query = count_query.where(Freelancer.is_active == is_active)

        count = session.exec(count_query).one()
        freelancers = session.exec(
            query.order_by(Freelancer.name).offset(skip).limit(limit)
        ).all()

        return FreelancersPublic(data=freelancers, count=count)

    @staticmethod
    def get_freelancer(session: Session, freelancer_id: uuid.UUID) -> FreelancerPublic:
        """Get a freelancer by ID."""
        freelancer = session.get(Freelancer, freelancer_id)
        if not freelancer:
            raise HTTPException(status_code=404, detail="Freelancer not found")
        return freelancer

    @staticmethod
    def create_freelancer(
        session: Session, freelancer_in: FreelancerCreate
    ) -> FreelancerPublic:
        """Create a new freelancer."""
        # Check for duplicate email
        existing = session.exec(
            select(Freelancer).where(Freelancer.email == freelancer_in.email)
        ).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="Freelancer with this email already exists"
            )

        freelancer = Freelancer.model_validate(freelancer_in)
        session.add(freelancer)
        session.commit()
        session.refresh(freelancer)
        return freelancer

    @staticmethod
    def update_freelancer(
        session: Session, freelancer_id: uuid.UUID, freelancer_in: FreelancerUpdate
    ) -> FreelancerPublic:
        """Update a freelancer."""
        freelancer = session.get(Freelancer, freelancer_id)
        if not freelancer:
            raise HTTPException(status_code=404, detail="Freelancer not found")

        # Check for duplicate email if updating
        if freelancer_in.email and freelancer_in.email != freelancer.email:
            existing = session.exec(
                select(Freelancer).where(Freelancer.email == freelancer_in.email)
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400, detail="Freelancer with this email already exists"
                )

        update_data = freelancer_in.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        freelancer.sqlmodel_update(update_data)
        session.add(freelancer)
        session.commit()
        session.refresh(freelancer)
        return freelancer

    @staticmethod
    def delete_freelancer(session: Session, freelancer_id: uuid.UUID) -> None:
        """Delete a freelancer."""
        freelancer = session.get(Freelancer, freelancer_id)
        if not freelancer:
            raise HTTPException(status_code=404, detail="Freelancer not found")
        session.delete(freelancer)
        session.commit()
