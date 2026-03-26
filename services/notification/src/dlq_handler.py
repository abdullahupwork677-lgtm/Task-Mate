"""Dead Letter Queue (DLQ) Handler

Phase V - Production Readiness
Task: T193, T194

Handles failed notifications by sending them to a dead letter queue after retries.
"""

from typing import Dict, Any
import json
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from src.utils.logger import get_logger
from src.utils.metrics import NotificationMetrics
from src.schemas import ReminderEvent

logger = get_logger(__name__)


class DLQHandler:
    """Handler for dead letter queue operations (T193, T194)."""
    
    def __init__(self, kafka_bootstrap_servers: str, dlq_topic: str = "reminders.dlq"):
        """Initialize DLQ handler.
        
        Args:
            kafka_bootstrap_servers: Kafka bootstrap servers
            dlq_topic: Dead letter queue topic name (default: reminders.dlq)
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.dlq_topic = dlq_topic
        self.producer = None
        self.max_retries = 3  # T194: Send to DLQ after 3 failed attempts
    
    async def initialize(self) -> None:
        """Initialize Kafka producer for DLQ."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info("dlq_producer_started", topic=self.dlq_topic)
        except Exception as e:
            logger.error("dlq_producer_start_failed", error=str(e))
            raise
    
    async def shutdown(self) -> None:
        """Shutdown DLQ producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("dlq_producer_stopped")
    
    async def send_to_dlq(
        self,
        event: ReminderEvent,
        error: str,
        retry_count: int,
        failure_reason: str
    ) -> None:
        """Send failed notification to dead letter queue (T194).
        
        Args:
            event: Original reminder event that failed
            error: Error message
            retry_count: Number of retries attempted
            failure_reason: Reason for DLQ (max_retries, parse_error, validation_error)
        
        Logic:
            - After 3 failed attempts, message is sent to DLQ
            - DLQ message includes original event + error metadata
            - Metrics are recorded for monitoring
        """
        try:
            # Create DLQ message with metadata
            dlq_message = {
                "original_event": event.model_dump() if hasattr(event, 'model_dump') else dict(event),
                "error": error,
                "retry_count": retry_count,
                "failure_reason": failure_reason,
                "dlq_timestamp": event.timestamp if hasattr(event, 'timestamp') else None
            }
            
            # Send to DLQ topic
            await self.producer.send_and_wait(
                self.dlq_topic,
                value=dlq_message
            )
            
            logger.warning(
                "message_sent_to_dlq",
                event_id=event.event_id,
                task_id=event.task_id,
                reason=failure_reason,
                retry_count=retry_count,
                error=error
            )
            
            # T187: Record DLQ metrics
            NotificationMetrics.record_dlq_message(reason=failure_reason)
            
        except KafkaError as e:
            logger.error(
                "dlq_send_failed",
                event_id=event.event_id,
                error=str(e)
            )
            # If DLQ send fails, log for manual intervention
            raise
    
    def should_send_to_dlq(self, retry_count: int) -> bool:
        """Check if message should be sent to DLQ (T194).
        
        Args:
            retry_count: Current retry count
            
        Returns:
            True if retry_count >= max_retries (3), False otherwise
        """
        return retry_count >= self.max_retries


# Retry logic with exponential backoff
class RetryHandler:
    """Handles retry logic with exponential backoff."""
    
    @staticmethod
    def calculate_backoff(retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """Calculate exponential backoff delay.
        
        Args:
            retry_count: Current retry attempt (0-indexed)
            base_delay: Base delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 60.0)
            
        Returns:
            Delay in seconds
            
        Example:
            Retry 0: 1s
            Retry 1: 2s
            Retry 2: 4s
            Retry 3: 8s (then DLQ)
        """
        delay = base_delay * (2 ** retry_count)
        return min(delay, max_delay)
