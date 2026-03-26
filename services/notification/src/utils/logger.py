"""Structured JSON Logging Configuration - Notification Service

Phase V - Production Readiness
Task: T182

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


def setup_json_logging(service_name: str = "notification-service", log_level: str = "INFO") -> None:
    """Configure structured JSON logging with structlog.
    
    Args:
        service_name: Name of the service (notification-service)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Usage:
        from src.utils.logger import setup_json_logging, get_logger
        
        setup_json_logging(service_name="notification-service", log_level="INFO")
        logger = get_logger(__name__)
        
        logger.info("notification_sent", channel="email", task_id=123)
        logger.error("kafka_error", error="Connection timeout")
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
        logger.info("email_sent", recipient="user@example.com", task_id=123)
        
        # Output:
        # {
        #   "event": "email_sent",
        #   "recipient": "user@example.com",
        #   "task_id": 123,
        #   "logger": "src.handlers.email_handler",
        #   "level": "info",
        #   "timestamp": "2024-02-14T12:00:00.000Z",
        #   "trace_id": "abc-def-123",
        #   "service": "notification-service"
        # }
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind additional context to all subsequent logs in this context.
    
    Args:
        **kwargs: Key-value pairs to bind (e.g., event_id="evt-123", task_id=456)
    
    Example:
        # In Kafka consumer
        bind_context(event_id=event.event_id, task_id=event.task_id)
        logger.info("processing_event")
        # All logs will include event_id and task_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*args: str) -> None:
    """Unbind context keys.
    
    Args:
        *args: Keys to unbind
    
    Example:
        unbind_context("event_id", "task_id")
    """
    structlog.contextvars.unbind_contextvars(*args)


def clear_context() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()


# T184: Notification Delivery Event Logger
class NotificationDeliveryLogger:
    """Structured logger for notification delivery events (T184)."""
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    def log_consumed(self, event_id: str, task_id: int, user_id: str, channels: list) -> None:
        """Log Kafka event consumption."""
        self.logger.info(
            "event_consumed",
            event_id=event_id,
            task_id=task_id,
            user_id=user_id,
            channels=channels,
            event_type="kafka_consume"
        )
    
    def log_delivery_start(self, event_id: str, task_id: int, channel: str) -> None:
        """Log notification delivery start."""
        self.logger.info(
            "notification_delivery_started",
            event_id=event_id,
            task_id=task_id,
            channel=channel,
            event_type="notification_delivery"
        )
    
    def log_delivery_success(
        self,
        event_id: str,
        task_id: int,
        user_id: str,
        channel: str,
        status: str,
        latency_ms: float
    ) -> None:
        """Log successful notification delivery (T184)."""
        self.logger.info(
            "notification_delivered",
            event_id=event_id,
            task_id=task_id,
            user_id=user_id,
            channel=channel,
            status=status,
            latency_ms=latency_ms,
            event_type="notification_delivery"
        )
    
    def log_delivery_failure(
        self,
        event_id: str,
        task_id: int,
        user_id: str,
        channel: str,
        error: str,
        latency_ms: float,
        retry_count: int = 0
    ) -> None:
        """Log notification delivery failure (T184)."""
        self.logger.error(
            "notification_delivery_failed",
            event_id=event_id,
            task_id=task_id,
            user_id=user_id,
            channel=channel,
            error=error,
            latency_ms=latency_ms,
            retry_count=retry_count,
            event_type="notification_delivery"
        )
    
    def log_dlq_sent(self, event_id: str, task_id: int, reason: str, retry_count: int) -> None:
        """Log message sent to dead letter queue (T194)."""
        self.logger.warning(
            "message_sent_to_dlq",
            event_id=event_id,
            task_id=task_id,
            reason=reason,
            retry_count=retry_count,
            event_type="dlq"
        )
