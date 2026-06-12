from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth, health, incidents, inventory, suppliers, users
from .core.config import get_settings
from .core.database import init_db
from .core.exception_handlers import register_exception_handlers


settings = get_settings()

app = FastAPI(
    title="TrackFlow API",
    version="0.1.0",
    description="Operational API for TrackFlow internal workflows.",
)

register_exception_handlers(app)

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(inventory.router, tags=["inventory"])
