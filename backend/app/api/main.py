from fastapi import APIRouter

from app.api.routes.auth import views as auth_views
from app.api.routes.items import views as items_views
from app.api.routes.payment_batches import router as payment_batches_router
from app.api.routes.private import views as private_views
from app.api.routes.users import views as users_views
from app.api.routes.utils import views as utils_views
from app.api.routes.worklogs import router as worklogs_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(auth_views.router)
api_router.include_router(users_views.router)
api_router.include_router(utils_views.router)
api_router.include_router(items_views.router)
api_router.include_router(worklogs_router.router)
api_router.include_router(payment_batches_router.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private_views.router)
