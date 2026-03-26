"""Prometheus Metrics for Backend API

Phase V - Production Readiness
Task: T186

Exports Prometheus metrics for monitoring and alerting.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional
import time


# T186: Backend Prometheus Metrics

# Reminder Check Metrics
reminder_checks_total = Counter(
    'reminder_checks_total',
    'Total number of reminder checks executed',
    ['status']  # Labels: success, error
)

reminders_sent_total = Counter(
    'reminders_sent_total',
    'Total number of reminders sent',
    ['reminder_type']  # Labels: 24h, 1h, 3d, custom
)

reminder_check_duration_seconds = Histogram(
    'reminder_check_duration_seconds',
    'Duration of reminder check operations in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Task Metrics
tasks_checked_gauge = Gauge(
    'tasks_checked_last_run',
    'Number of tasks checked in last reminder run'
)

# Error Metrics
reminder_errors_total = Counter(
    'reminder_errors_total',
    'Total number of errors during reminder checks',
    ['error_type']  # Labels: database_error, kafka_error, validation_error
)


class ReminderMetrics:
    """Helper class for recording reminder-related metrics (T186)."""
    
    @staticmethod
    def record_check_start() -> float:
        """Record the start of a reminder check.
        
        Returns:
            start_time: Timestamp to measure duration
        """
        return time.time()
    
    @staticmethod
    def record_check_complete(
        start_time: float,
        tasks_checked: int,
        reminders_sent: int,
        status: str = "success"
    ) -> None:
        """Record completion of reminder check (T186).
        
        Args:
            start_time: Start timestamp from record_check_start()
            tasks_checked: Number of tasks processed
            reminders_sent: Number of reminders sent
            status: Status of check (success, error)
        """
        # Duration metric
        duration = time.time() - start_time
        reminder_check_duration_seconds.observe(duration)
        
        # Count metric
        reminder_checks_total.labels(status=status).inc()
        
        # Gauge metric
        tasks_checked_gauge.set(tasks_checked)
    
    @staticmethod
    def record_reminder_sent(reminder_type: str) -> None:
        """Record a reminder sent (T186).
        
        Args:
            reminder_type: Type of reminder (24h, 1h, 3d, custom)
        """
        reminders_sent_total.labels(reminder_type=reminder_type).inc()
    
    @staticmethod
    def record_error(error_type: str) -> None:
        """Record an error during reminder check.
        
        Args:
            error_type: Type of error (database_error, kafka_error, validation_error)
        """
        reminder_errors_total.labels(error_type=error_type).inc()


def get_metrics() -> tuple[bytes, str]:
    """Get Prometheus metrics in exposition format (T188).
    
    Returns:
        Tuple of (metrics_data, content_type)
        
    Usage:
        from fastapi import Response
        from src.utils.metrics import get_metrics
        
        @app.get("/metrics")
        def metrics():
            data, content_type = get_metrics()
            return Response(content=data, media_type=content_type)
    """
    return generate_latest(), CONTENT_TYPE_LATEST
