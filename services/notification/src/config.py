"""Notification Service Configuration

Configuration for Kafka, SendGrid (email), Firebase (push notifications),
and database connection.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
Task: T091
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Notification Microservice"
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        validation_alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_topic_reminders: str = Field(
        default="reminders",
        validation_alias="KAFKA_TOPIC_REMINDERS"
    )
    kafka_consumer_group: str = Field(
        default="notification-service-group",
        validation_alias="KAFKA_CONSUMER_GROUP"
    )

    # SendGrid Configuration (Email)
    sendgrid_api_key: str = Field(
        default="",
        validation_alias="SENDGRID_API_KEY"
    )
    sendgrid_from_email: str = Field(
        default="noreply@todoapp.com",
        validation_alias="SENDGRID_FROM_EMAIL"
    )
    sendgrid_from_name: str = Field(
        default="Todo App Reminders",
        validation_alias="SENDGRID_FROM_NAME"
    )

    # Firebase Configuration (Push Notifications)
    firebase_credentials_path: str = Field(
        default="",
        validation_alias="FIREBASE_CREDENTIALS_PATH"
    )
    firebase_project_id: str = Field(
        default="",
        validation_alias="FIREBASE_PROJECT_ID"
    )

    # Database Configuration (for logging notifications)
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/todo_db",
        validation_alias="DATABASE_URL"
    )

    # Notification Settings
    retry_attempts: int = Field(
        default=3,
        validation_alias="NOTIFICATION_RETRY_ATTEMPTS"
    )
    retry_delay_seconds: int = Field(
        default=1,
        validation_alias="NOTIFICATION_RETRY_DELAY_SECONDS"
    )

    # Consumer Settings
    consumer_fetch_max_bytes: int = Field(
        default=1048576,  # 1MB
        validation_alias="KAFKA_CONSUMER_FETCH_MAX_BYTES"
    )
    consumer_max_poll_records: int = Field(
        default=500,
        validation_alias="KAFKA_CONSUMER_MAX_POLL_RECORDS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Validation: Log configuration on startup
def validate_settings():
    """Validate critical configuration on startup."""
    errors = []

    if not settings.kafka_bootstrap_servers:
        errors.append("KAFKA_BOOTSTRAP_SERVERS is required")

    if not settings.sendgrid_api_key:
        errors.append("SENDGRID_API_KEY is required for email notifications")

    if not settings.database_url:
        errors.append("DATABASE_URL is required for notification logging")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Log configuration summary (non-sensitive info only)
def log_settings():
    """Log configuration summary."""
    import logging
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Notification Service Configuration:")
    logger.info(f"  Kafka Bootstrap: {settings.kafka_bootstrap_servers}")
    logger.info(f"  Kafka Topic: {settings.kafka_topic_reminders}")
    logger.info(f"  Consumer Group: {settings.kafka_consumer_group}")
    logger.info(f"  SendGrid From: {settings.sendgrid_from_email}")
    logger.info(f"  Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'N/A'}")
    logger.info(f"  Retry Attempts: {settings.retry_attempts}")
    logger.info("=" * 60)
