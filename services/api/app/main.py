from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import auth, health, incidents, users
from .core.config import get_settings
from .core.database import init_db


settings = get_settings()

app = FastAPI(
    title="TrackFlow API",
    version="0.1.0",
    description="Operational API for TrackFlow internal workflows.",
)

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
