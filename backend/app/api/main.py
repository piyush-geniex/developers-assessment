from fastapi import APIRouter

from app.api.routes.auth import views as auth_views
from app.api.routes.freelancer_auth import views as freelancer_auth_views
from app.api.routes.freelancer_portal import views as freelancer_portal_views
from app.api.routes.freelancers import views as freelancers_views
from app.api.routes.items import views as items_views
from app.api.routes.payments import views as payments_views
from app.api.routes.private import views as private_views
from app.api.routes.time_entries import views as time_entries_views
from app.api.routes.users import views as users_views
from app.api.routes.utils import views as utils_views
from app.api.routes.worklogs import views as worklogs_views
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(auth_views.router)
api_router.include_router(users_views.router)
api_router.include_router(utils_views.router)
api_router.include_router(items_views.router)
api_router.include_router(freelancers_views.router)
api_router.include_router(worklogs_views.router)
api_router.include_router(time_entries_views.router)
api_router.include_router(payments_views.router)

# Freelancer portal routes (separate auth system)
api_router.include_router(freelancer_auth_views.router)
api_router.include_router(freelancer_portal_views.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private_views.router)
