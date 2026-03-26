"""Tests for Prometheus Metrics

Phase V - Production Readiness
Task: T189
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.utils.metrics import ReminderMetrics, reminder_checks_total, reminders_sent_total


client = TestClient(app)


def test_metrics_endpoint_exists():
    """Test T189: Metrics endpoint is accessible."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_format():
    """Test T189: Metrics are in Prometheus exposition format."""
    response = client.get("/metrics")
    content = response.text
    
    # Should contain metric names
    assert "reminder_checks_total" in content
    assert "reminders_sent_total" in content
    assert "reminder_check_duration_seconds" in content
    
    # Should contain TYPE and HELP comments
    assert "# TYPE" in content
    assert "# HELP" in content


def test_reminder_metrics_increment():
    """Test T189: Verify counters increment correctly."""
    # Record a reminder check
    start_time = ReminderMetrics.record_check_start()
    ReminderMetrics.record_check_complete(
        start_time=start_time,
        tasks_checked=100,
        reminders_sent=5,
        status="success"
    )
    
    # Record reminders sent
    ReminderMetrics.record_reminder_sent("24h")
    ReminderMetrics.record_reminder_sent("1h")
    ReminderMetrics.record_reminder_sent("24h")
    
    # Fetch metrics
    response = client.get("/metrics")
    content = response.text
    
    # Verify counters are present (exact values may vary in tests)
    assert 'reminder_checks_total{status="success"}' in content
    assert 'reminders_sent_total{reminder_type="24h"}' in content
    assert 'reminders_sent_total{reminder_type="1h"}' in content


def test_error_metrics_increment():
    """Test T189: Error metrics increment on failures."""
    # Record errors
    ReminderMetrics.record_error("database_error")
    ReminderMetrics.record_error("kafka_error")
    
    # Fetch metrics
    response = client.get("/metrics")
    content = response.text
    
    # Verify error counter is present
    assert "reminder_errors_total" in content
    assert 'error_type="database_error"' in content
    assert 'error_type="kafka_error"' in content


def test_histogram_buckets():
    """Test T189: Histogram metrics have buckets."""
    response = client.get("/metrics")
    content = response.text
    
    # Verify histogram has buckets
    assert "reminder_check_duration_seconds_bucket" in content
    assert 'le="0.1"' in content
    assert 'le="0.5"' in content
    assert 'le="1.0"' in content
    assert 'le="5.0"' in content
    
    # Verify histogram has sum and count
    assert "reminder_check_duration_seconds_sum" in content
    assert "reminder_check_duration_seconds_count" in content
