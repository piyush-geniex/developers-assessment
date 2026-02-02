"""
Freelancers API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import uuid

from ..database import get_session
from ..models import Freelancer, FreelancerRead

router = APIRouter(prefix="/api/freelancers", tags=["freelancers"])


@router.get("", response_model=List[FreelancerRead])
async def get_freelancers(
    session: Session = Depends(get_session)
) -> List[FreelancerRead]:
    """
    Get all freelancers
    """
    statement = select(Freelancer).order_by(Freelancer.name)
    freelancers = session.exec(statement).all()
    return [FreelancerRead.model_validate(f) for f in freelancers]


@router.get("/{freelancer_id}", response_model=FreelancerRead)
async def get_freelancer(
    freelancer_id: uuid.UUID,
    session: Session = Depends(get_session)
) -> FreelancerRead:
    """
    Get a specific freelancer by ID
    """
    freelancer = session.get(Freelancer, freelancer_id)
    if not freelancer:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    return FreelancerRead.model_validate(freelancer)
