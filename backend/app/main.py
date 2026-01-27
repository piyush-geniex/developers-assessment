import sentry_sdk
from fastapi import FastAPI, Depends
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

from sqlmodel import Session, select
from app.core.db import get_session

from app.services.settlement import run_settlement
from app.models import WorkLog, Remittance

from datetime import datetime

app = FastAPI()


def custom_generate_unique_id(route: APIRoute) -> str:
    # return f"{route.tags[0]}-{route.name}"
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"

if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)



@app.post("/generate-remittances-for-all-users",
    tags=["remittances"],
    )
def generate_remittances(start: str, end: str, session: Session = Depends(get_session)):
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    remittances = run_settlement(session, start_dt, end_dt)
    return {"remittances": [r.model_dump() for r in remittances]}

@app.get("/list-all-worklogs",
    tags=["worklogs"],)
def list_worklogs(remittanceStatus: str = None, session: Session = Depends(get_session)):
    query = select(WorkLog)
    if remittanceStatus is not None:
        query = query.where(WorkLog.is_settled == (remittanceStatus == "REMITTED"))
    logs = session.exec(query).all()
    return {"worklogs": logs}
