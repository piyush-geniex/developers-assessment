"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import create_db_and_tables
from .routers import worklogs_router, freelancers_router, payments_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting WorkLog Payment Dashboard API...")
    create_db_and_tables()
    print("✅ Database tables ready")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="Admin dashboard API for managing freelancer worklogs and processing payments",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(worklogs_router)
app.include_router(freelancers_router)
app.include_router(payments_router)


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "api": "operational"
    }
