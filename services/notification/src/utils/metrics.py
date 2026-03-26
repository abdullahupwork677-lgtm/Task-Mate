"""Prometheus Metrics for Notification Service

Phase V - Production Readiness
Task: T187

Exports Prometheus metrics for monitoring notification delivery.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time


# T187: Notification Service Prometheus Metrics

# Notification Delivery Metrics
notifications_sent_total = Counter(
    'notifications_sent_total',
    'Total number of notifications sent',
    ['channel', 'status']  # Labels: (email/push/in_app, success/failed)
)

notification_delivery_latency_seconds = Histogram(
    'notification_delivery_latency_seconds',
    'Latency of notification delivery in seconds',
    ['channel'],  # Labels: email, push, in_app
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

notification_failures_total = Counter(
    'notification_failures_total',
    'Total number of notification delivery failures',
    ['channel', 'error_type']  # Labels: (email/push/in_app, timeout/auth/network)
)

# Kafka Consumer Metrics
kafka_messages_consumed_total = Counter(
    'kafka_messages_consumed_total',
    'Total number of Kafka messages consumed',
    ['topic']  # Labels: reminders, reminders.dlq
)

kafka_consumer_lag_gauge = Gauge(
    'kafka_consumer_lag',
    'Current Kafka consumer lag (messages behind)'
)

# Dead Letter Queue Metrics
dlq_messages_total = Counter(
    'dlq_messages_total',
    'Total number of messages sent to dead letter queue',
    ['reason']  # Labels: max_retries, parse_error, validation_error
)

dlq_size_gauge = Gauge(
    'dlq_size',
    'Current number of messages in dead letter queue'
)


class NotificationMetrics:
    """Helper class for recording notification metrics (T187)."""
    
    @staticmethod
    def record_delivery_start(channel: str) -> float:
        """Record the start of notification delivery.
        
        Args:
            channel: Notification channel (email, push, in_app)
            
        Returns:
            start_time: Timestamp to measure latency
        """
        return time.time()
    
    @staticmethod
    def record_delivery_success(
        channel: str,
        start_time: float
    ) -> None:
        """Record successful notification delivery (T187).
        
        Args:
            channel: Notification channel (email, push, in_app)
            start_time: Start timestamp from record_delivery_start()
        """
        # Latency metric
        latency = time.time() - start_time
        notification_delivery_latency_seconds.labels(channel=channel).observe(latency)
        
        # Success counter
        notifications_sent_total.labels(channel=channel, status="success").inc()
    
    @staticmethod
    def record_delivery_failure(
        channel: str,
        error_type: str,
        start_time: float
    ) -> None:
        """Record failed notification delivery (T187).
        
        Args:
            channel: Notification channel (email, push, in_app)
            error_type: Type of error (timeout, auth, network, parse, validation)
            start_time: Start timestamp from record_delivery_start()
        """
        # Latency metric (even for failures)
        latency = time.time() - start_time
        notification_delivery_latency_seconds.labels(channel=channel).observe(latency)
        
        # Failure counters
        notifications_sent_total.labels(channel=channel, status="failed").inc()
        notification_failures_total.labels(channel=channel, error_type=error_type).inc()
    
    @staticmethod
    def record_kafka_message_consumed(topic: str = "reminders") -> None:
        """Record Kafka message consumption.
        
        Args:
            topic: Kafka topic name (reminders, reminders.dlq)
        """
        kafka_messages_consumed_total.labels(topic=topic).inc()
    
    @staticmethod
    def record_dlq_message(reason: str) -> None:
        """Record message sent to dead letter queue (T187).
        
        Args:
            reason: Reason for DLQ (max_retries, parse_error, validation_error)
        """
        dlq_messages_total.labels(reason=reason).inc()
    
    @staticmethod
    def update_dlq_size(size: int) -> None:
        """Update dead letter queue size gauge.
        
        Args:
            size: Current number of messages in DLQ
        """
        dlq_size_gauge.set(size)


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
