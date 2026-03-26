"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.logging_config import setup_logging
from src.middleware.error_handler import setup_error_handlers

# Setup structured JSON logging for production
setup_logging()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Todo API - Phase 2 Hackathon",
    version="0.1.0",
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup global error handlers
setup_error_handlers(app)

# Register routes
from src.routes import auth, health, tasks, chat, conversations, voice, reminders, notification_preferences, in_app_notifications, metrics

app.include_router(health.router)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(tasks.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)
app.include_router(conversations.router)
app.include_router(voice.router)
app.include_router(reminders.router)  # Internal Dapr endpoints
app.include_router(notification_preferences.router)  # Phase V - US5: Notification preferences
app.include_router(in_app_notifications.router)  # Phase V - US5: In-app notifications
app.include_router(metrics.router)  # Phase V - T188: Prometheus metrics


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Todo API - Backend Foundation",
        "version": "0.1.0",
        "docs": "/docs"
    }

