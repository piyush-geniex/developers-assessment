from fastapi import APIRouter
from app.api.deps import SessionDep
from app.api.routes.worklogs.service import WorkLogService
from app.models import WorkLogsPublic, Message
import uuid

router = APIRouter(prefix="/worklogs", tags=["worklogs"])

@router.get("/", response_model=WorkLogsPublic)
def list_worklogs(session: SessionDep, skip: int = 0, limit: int = 100):
    return WorkLogService.get_worklogs(session, skip, limit)

@router.patch("/{id}/pay", response_model=Message)
def pay_worklog(session: SessionDep, id: uuid.UUID):
    return WorkLogService.pay_worklog(session, id)