"""Structured JSON Logging Configuration

Phase V - Production Readiness
Task: T181

Provides JSON-formatted logging with trace_id for correlation across services.
"""

import logging
import structlog
from typing import Any, Dict
import uuid
from datetime import datetime


def add_trace_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add trace_id to log context for distributed tracing."""
    if "trace_id" not in event_dict:
        event_dict["trace_id"] = str(uuid.uuid4())
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add ISO 8601 timestamp to log."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def setup_json_logging(service_name: str = "backend-api", log_level: str = "INFO") -> None:
    """Configure structured JSON logging with structlog.
    
    Args:
        service_name: Name of the service (backend-api, notification-service)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Usage:
        from src.utils.logger import setup_json_logging, get_logger
        
        setup_json_logging(service_name="backend-api", log_level="INFO")
        logger = get_logger(__name__)
        
        logger.info("reminder_check_started", tasks_checked=100)
        logger.error("notification_failed", task_id=123, error="SendGrid timeout")
    """
    
    # Configure structlog processors
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            add_timestamp,
            add_trace_id,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
    )
    
    # Add service_name to all logs
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        structlog.BoundLogger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("user_created", user_id="user-123", email="user@example.com")
        
        # Output:
        # {
        #   "event": "user_created",
        #   "user_id": "user-123",
        #   "email": "user@example.com",
        #   "logger": "src.routes.auth",
        #   "level": "info",
        #   "timestamp": "2024-02-14T12:00:00.000Z",
        #   "trace_id": "abc-def-123",
        #   "service": "backend-api"
        # }
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind additional context to all subsequent logs in this context.
    
    Args:
        **kwargs: Key-value pairs to bind (e.g., user_id="user-123", request_id="req-456")
    
    Example:
        # In a FastAPI dependency
        @app.middleware("http")
        async def add_request_context(request: Request, call_next):
            request_id = str(uuid.uuid4())
            bind_context(request_id=request_id, path=request.url.path)
            response = await call_next(request)
            return response
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*args: str) -> None:
    """Unbind context keys.
    
    Args:
        *args: Keys to unbind
    
    Example:
        unbind_context("request_id", "user_id")
    """
    structlog.contextvars.unbind_contextvars(*args)


def clear_context() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()


# T183: Reminder Check Event Logger
class ReminderCheckLogger:
    """Structured logger for reminder check events."""
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    def log_start(self, tasks_to_check: int) -> None:
        """Log reminder check start."""
        self.logger.info(
            "reminder_check_started",
            tasks_to_check=tasks_to_check,
            event_type="reminder_check"
        )
    
    def log_complete(
        self,
        tasks_checked: int,
        reminders_sent: int,
        duration_ms: float,
        errors: int = 0
    ) -> None:
        """Log reminder check completion (T183)."""
        self.logger.info(
            "reminder_check_completed",
            tasks_checked=tasks_checked,
            reminders_sent=reminders_sent,
            duration_ms=duration_ms,
            errors=errors,
            event_type="reminder_check"
        )
    
    def log_error(self, error: str, task_id: int = None) -> None:
        """Log reminder check error."""
        self.logger.error(
            "reminder_check_error",
            error=error,
            task_id=task_id,
            event_type="reminder_check"
        )


# T184: Notification Delivery Event Logger
class NotificationDeliveryLogger:
    """Structured logger for notification delivery events."""
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    def log_sent(
        self,
        event_id: str,
        task_id: int,
        user_id: str,
        channel: str,
        status: str,
        latency_ms: float
    ) -> None:
        """Log notification delivery (T184)."""
        self.logger.info(
            "notification_sent",
            event_id=event_id,
            task_id=task_id,
            user_id=user_id,
            channel=channel,
            status=status,
            latency_ms=latency_ms,
            event_type="notification_delivery"
        )
    
    def log_failed(
        self,
        event_id: str,
        task_id: int,
        user_id: str,
        channel: str,
        error: str,
        latency_ms: float
    ) -> None:
        """Log notification delivery failure."""
        self.logger.error(
            "notification_failed",
            event_id=event_id,
            task_id=task_id,
            user_id=user_id,
            channel=channel,
            error=error,
            latency_ms=latency_ms,
            event_type="notification_delivery"
        )
