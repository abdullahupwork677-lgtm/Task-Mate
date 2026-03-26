"""Notification Microservice

Consumes reminder events from Kafka and sends notifications via email, push, and in-app.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
Task: T090, T182, T187, T188, T190
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from sqlmodel import create_engine, Session

from config import settings
from kafka_consumer import consume_reminder_events
from src.utils.logger import setup_json_logging, get_logger
from src.utils.metrics import get_metrics

# T182: Setup structured JSON logging
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_json_logging(service_name="notification-service", log_level=log_level)
logger = get_logger(__name__)

# Background task handle
consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Starts Kafka consumer on startup, stops on shutdown.
    """
    global consumer_task

    logger.info("Starting Notification Microservice...")

    # Start Kafka consumer in background
    logger.info("Starting Kafka consumer for reminder events...")
    consumer_task = asyncio.create_task(consume_reminder_events())

    logger.info("Notification service ready")

    yield

    # Shutdown
    logger.info("Shutting down Notification Microservice...")

    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Kafka consumer stopped")

    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Notification Microservice",
    description="Consumes reminder events and sends notifications",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Notification Microservice",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint (T190).

    Checks:
    - Kafka connectivity (consumer task running)
    - Database connectivity (can execute query)

    Returns:
        200 OK if all checks pass
        503 Service Unavailable if any check fails
    """
    checks = {
        "kafka": "unknown",
        "database": "unknown",
        "consumer_running": False
    }

    # Check 1: Kafka consumer running
    checks["consumer_running"] = consumer_task is not None and not consumer_task.done()
    checks["kafka"] = "connected" if checks["consumer_running"] else "disconnected"

    # Check 2: Database connectivity (T190)
    try:
        engine = create_engine(settings.database_url)
        with Session(engine) as session:
            session.execute("SELECT 1")
        checks["database"] = "connected"
    except Exception as e:
        logger.error("health_check_database_failed", error=str(e))
        checks["database"] = "disconnected"

    # Determine overall status
    is_healthy = checks["kafka"] == "connected" and checks["database"] == "connected"
    status_code = 200 if is_healthy else 503

    return Response(
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "checks": checks
        },
        status_code=status_code,
        media_type="application/json"
    )


@app.get("/metrics")
def prometheus_metrics():
    """Prometheus metrics endpoint (T188).

    Exposes metrics for scraping:
    - notifications_sent_total
    - notification_delivery_latency_seconds
    - notification_failures_total
    - kafka_messages_consumed_total
    - dlq_messages_total

    Example usage:
        curl http://localhost:8001/metrics

    Prometheus configuration:
        scrape_configs:
          - job_name: 'notification-service'
            static_configs:
              - targets: ['notification-service:8001']
            metrics_path: /metrics
            scrape_interval: 15s
    """
    data, content_type = get_metrics()
    return Response(content=data, media_type=content_type)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Different port from backend (8000)
        reload=True,
        log_level="info"
    )
