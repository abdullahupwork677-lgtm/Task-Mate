"""Structured JSON logging configuration for production.

Phase V - Production Readiness
Task: T181, T183
"""

import os
from src.utils.logger import setup_json_logging


def setup_logging():
    """Configure structured JSON logging for production observability (T181).

    Sets up JSON-formatted logging to stdout with trace_id for correlation
    across services. Compatible with log aggregation tools (DataDog, Splunk, CloudWatch).

    Environment Variables:
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR) - defaults to INFO
        SERVICE_NAME: Service name for logs - defaults to "backend-api"
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")
    service_name = os.getenv("SERVICE_NAME", "backend-api")

    # Initialize structlog-based JSON logging
    setup_json_logging(service_name=service_name, log_level=log_level)

    return None  # structlog doesn't use root logger
