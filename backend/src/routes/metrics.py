"""Prometheus Metrics Endpoint

Phase V - Production Readiness
Task: T188

Exposes /metrics endpoint for Prometheus scraping.
"""

from fastapi import APIRouter, Response
from src.utils.metrics import get_metrics

router = APIRouter(tags=["observability"])


@router.get("/metrics")
def prometheus_metrics() -> Response:
    """Prometheus metrics endpoint (T188).
    
    Returns:
        Response with Prometheus exposition format metrics
        
    Example metrics:
        # HELP reminder_checks_total Total number of reminder checks executed
        # TYPE reminder_checks_total counter
        reminder_checks_total{status="success"} 42.0
        
        # HELP reminders_sent_total Total number of reminders sent
        # TYPE reminders_sent_total counter
        reminders_sent_total{reminder_type="24h"} 100.0
        reminders_sent_total{reminder_type="1h"} 85.0
        
        # HELP reminder_check_duration_seconds Duration of reminder check operations
        # TYPE reminder_check_duration_seconds histogram
        reminder_check_duration_seconds_bucket{le="0.5"} 20.0
        reminder_check_duration_seconds_bucket{le="1.0"} 35.0
        reminder_check_duration_seconds_sum 45.6
        reminder_check_duration_seconds_count 42.0
        
    Usage:
        # Scrape with Prometheus
        curl http://localhost:8000/metrics
        
        # Prometheus configuration (prometheus.yml)
        scrape_configs:
          - job_name: 'backend-api'
            static_configs:
              - targets: ['backend-api:8000']
            metrics_path: /metrics
            scrape_interval: 15s
    """
    data, content_type = get_metrics()
    return Response(content=data, media_type=content_type)
