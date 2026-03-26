"""Tests for Multi-Channel Notification Orchestration

Tests parallel delivery across email, push, and in-app channels.

Phase V - Due Dates & Reminders
User Story 5: Multi-Channel Notifications
Tasks: T153-T154
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from zoneinfo import ZoneInfo

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kafka_consumer import route_to_handlers
from schemas import ReminderEvent, NotificationLogEntry


@pytest.fixture
def sample_reminder_event():
    """Create a sample ReminderEvent for testing."""
    return ReminderEvent(
        event_id="test-multi-channel-123",
        task_id=42,
        task_title="Submit project report",
        task_description="Q4 financial report",
        user_id="user-123",
        due_date="2026-02-20T17:00:00+00:00",
        reminder_type="24h",
        channels=["email", "push", "in_app"],
        priority="high"
    )


@pytest.fixture
def all_channels_event():
    """Event with all channels enabled."""
    return ReminderEvent(
        event_id="test-all-channels",
        task_id=50,
        task_title="Board meeting",
        task_description="Prepare presentation",
        user_id="user-456",
        due_date="2026-02-21T15:00:00+00:00",
        reminder_type="1h",
        channels=["email", "push", "in_app"],
        priority="high"
    )


class TestMultiChannelOrchestration:
    """Tests for T153-T154: Multi-channel notification orchestration."""

    @pytest.mark.asyncio
    async def test_all_channels_deliver_successfully(self, all_channels_event):
        """Test T153: User with all channels enabled receives notifications simultaneously.

        Scenario:
        - User has all 3 channels enabled: email, push, in_app
        - All handlers succeed
        - All 3 notifications delivered
        - Delivery happens in parallel (fast)

        Expected:
        - 3 results returned (one per channel)
        - All results have status="success"
        - Total duration < 3x individual handler time (proves parallelism)
        """
        # Mock handler responses (all succeed)
        mock_email_result = {
            "status": "success",
            "sent_at": datetime.now(ZoneInfo("UTC")).isoformat()
        }
        mock_push_result = NotificationLogEntry(
            task_id=all_channels_event.task_id,
            user_id=all_channels_event.user_id,
            reminder_type=all_channels_event.reminder_type,
            channel="push",
            status="success",
            sent_at=datetime.now(ZoneInfo("UTC")),
            error_message=None,
            event_id=all_channels_event.event_id
        )
        mock_in_app_result = NotificationLogEntry(
            task_id=all_channels_event.task_id,
            user_id=all_channels_event.user_id,
            reminder_type=all_channels_event.reminder_type,
            channel="in_app",
            status="success",
            sent_at=datetime.now(ZoneInfo("UTC")),
            error_message=None,
            event_id=all_channels_event.event_id
        )

        # Patch all handler wrappers
        with patch('kafka_consumer._send_email_wrapper', new_callable=AsyncMock) as mock_email, \
             patch('kafka_consumer._send_push_wrapper', new_callable=AsyncMock) as mock_push, \
             patch('kafka_consumer._send_in_app_wrapper', new_callable=AsyncMock) as mock_in_app:

            # Configure mocks
            mock_email.return_value = mock_email_result
            mock_push.return_value = {
                "status": mock_push_result.status,
                "sent_at": mock_push_result.sent_at.isoformat(),
                "error": mock_push_result.error_message
            }
            mock_in_app.return_value = {
                "status": mock_in_app_result.status,
                "sent_at": mock_in_app_result.sent_at.isoformat(),
                "error": mock_in_app_result.error_message
            }

            # Add artificial delay to prove parallel execution
            async def delayed_email(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms
                return mock_email_result

            async def delayed_push(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms
                return {
                    "status": mock_push_result.status,
                    "sent_at": mock_push_result.sent_at.isoformat(),
                    "error": mock_push_result.error_message
                }

            async def delayed_in_app(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms
                return {
                    "status": mock_in_app_result.status,
                    "sent_at": mock_in_app_result.sent_at.isoformat(),
                    "error": mock_in_app_result.error_message
                }

            mock_email.side_effect = delayed_email
            mock_push.side_effect = delayed_push
            mock_in_app.side_effect = delayed_in_app

            # Execute multi-channel delivery
            start_time = datetime.now(ZoneInfo("UTC"))
            results = await route_to_handlers(all_channels_event)
            end_time = datetime.now(ZoneInfo("UTC"))

            duration_ms = (end_time - start_time).total_seconds() * 1000

            # T153: Verify all 3 channels delivered
            assert len(results) == 3, f"Expected 3 results, got {len(results)}"

            # Extract channel names from results
            channel_names = [r["channel"] for r in results]
            assert "email" in channel_names
            assert "push" in channel_names
            assert "in_app" in channel_names

            # T153: Verify all succeeded
            for result in results:
                assert result["status"] == "success", \
                    f"Channel {result['channel']} failed: {result.get('error')}"

            # T153: Verify parallel execution (should be ~100ms, not 300ms)
            # Each handler has 100ms delay, but with parallel execution total should be ~100ms
            # Allow margin for overhead (expect < 200ms)
            assert duration_ms < 200, \
                f"Parallel execution too slow: {duration_ms:.2f}ms (expected ~100ms). " \
                f"Indicates sequential execution!"

            # Verify all handlers were called
            assert mock_email.called
            assert mock_push.called
            assert mock_in_app.called

    @pytest.mark.asyncio
    async def test_one_channel_fails_others_still_deliver(self, sample_reminder_event):
        """Test T154: One channel fails → Other channels still deliver.

        Scenario:
        - User has 3 channels enabled: email, push, in_app
        - Push notification fails (e.g., no FCM token, network error)
        - Email and in-app still succeed

        Expected:
        - 3 results returned
        - Push result has status="error"
        - Email and in-app have status="success"
        - No exception raised (failure isolated)
        """
        # Mock handler responses
        mock_email_result = {
            "status": "success",
            "sent_at": datetime.now(ZoneInfo("UTC")).isoformat()
        }
        mock_in_app_result = {
            "status": "success",
            "sent_at": datetime.now(ZoneInfo("UTC")).isoformat(),
            "error": None
        }

        # Patch all handler wrappers
        with patch('kafka_consumer._send_email_wrapper', new_callable=AsyncMock) as mock_email, \
             patch('kafka_consumer._send_push_wrapper', new_callable=AsyncMock) as mock_push, \
             patch('kafka_consumer._send_in_app_wrapper', new_callable=AsyncMock) as mock_in_app:

            # Configure mocks
            mock_email.return_value = mock_email_result
            mock_in_app.return_value = mock_in_app_result

            # T154: Push fails with exception
            mock_push.side_effect = Exception("Firebase connection timeout")

            # Execute multi-channel delivery
            results = await route_to_handlers(sample_reminder_event)

            # T154: Verify all 3 channels attempted
            assert len(results) == 3, f"Expected 3 results, got {len(results)}"

            # Find results by channel
            results_by_channel = {r["channel"]: r for r in results}

            # T154: Verify email succeeded
            assert "email" in results_by_channel
            assert results_by_channel["email"]["status"] == "success"

            # T154: Verify push failed (but didn't crash)
            assert "push" in results_by_channel
            assert results_by_channel["push"]["status"] == "error"
            assert "Firebase connection timeout" in results_by_channel["push"]["error"]

            # T154: Verify in-app succeeded (not affected by push failure)
            assert "in_app" in results_by_channel
            assert results_by_channel["in_app"]["status"] == "success"

            # Verify all handlers were called despite failure
            assert mock_email.called
            assert mock_push.called
            assert mock_in_app.called

    @pytest.mark.asyncio
    async def test_multiple_channels_fail_at_least_one_succeeds(self):
        """Test T154 edge case: Multiple channels fail, at least one succeeds.

        Scenario:
        - All 3 channels enabled
        - Email fails (SMTP error)
        - Push fails (no FCM token)
        - In-app succeeds

        Expected:
        - 3 results returned
        - Email status="error"
        - Push status="error"
        - In-app status="success"
        - Overall status should be success (at least one delivered)
        """
        event = ReminderEvent(
            event_id="test-partial-failure",
            task_id=99,
            task_title="Critical task",
            task_description="Urgent!",
            user_id="user-789",
            due_date="2026-02-22T09:00:00+00:00",
            reminder_type="1h",
            channels=["email", "push", "in_app"],
            priority="high"
        )

        mock_in_app_result = {
            "status": "success",
            "sent_at": datetime.now(ZoneInfo("UTC")).isoformat(),
            "error": None
        }

        with patch('kafka_consumer._send_email_wrapper', new_callable=AsyncMock) as mock_email, \
             patch('kafka_consumer._send_push_wrapper', new_callable=AsyncMock) as mock_push, \
             patch('kafka_consumer._send_in_app_wrapper', new_callable=AsyncMock) as mock_in_app:

            # Email and push fail
            mock_email.side_effect = Exception("SMTP connection refused")
            mock_push.side_effect = Exception("No FCM token available")

            # In-app succeeds
            mock_in_app.return_value = mock_in_app_result

            # Execute
            results = await route_to_handlers(event)

            # Verify
            assert len(results) == 3

            results_by_channel = {r["channel"]: r for r in results}

            # Email failed
            assert results_by_channel["email"]["status"] == "error"
            assert "SMTP" in results_by_channel["email"]["error"]

            # Push failed
            assert results_by_channel["push"]["status"] == "error"
            assert "FCM token" in results_by_channel["push"]["error"]

            # In-app succeeded
            assert results_by_channel["in_app"]["status"] == "success"

            # At least one channel delivered successfully
            success_count = sum(1 for r in results if r["status"] == "success")
            assert success_count >= 1, "At least one channel should succeed"

    @pytest.mark.asyncio
    async def test_parallel_execution_performance(self):
        """Test T153: Verify parallel execution is actually faster than sequential.

        Scenario:
        - 3 channels, each with 100ms artificial delay
        - Sequential: ~300ms total
        - Parallel: ~100ms total

        Expected:
        - Total execution time < 150ms (proves parallelism)
        """
        event = ReminderEvent(
            event_id="test-performance",
            task_id=77,
            task_title="Performance test",
            user_id="user-perf",
            due_date="2026-02-23T12:00:00+00:00",
            reminder_type="24h",
            channels=["email", "push", "in_app"],
            priority="medium"
        )

        DELAY_MS = 100

        with patch('kafka_consumer._send_email_wrapper', new_callable=AsyncMock) as mock_email, \
             patch('kafka_consumer._send_push_wrapper', new_callable=AsyncMock) as mock_push, \
             patch('kafka_consumer._send_in_app_wrapper', new_callable=AsyncMock) as mock_in_app:

            # Add delays to all handlers
            async def delayed_handler(*args, **kwargs):
                await asyncio.sleep(DELAY_MS / 1000)  # Convert to seconds
                return {
                    "status": "success",
                    "sent_at": datetime.now(ZoneInfo("UTC")).isoformat()
                }

            mock_email.side_effect = delayed_handler
            mock_push.side_effect = delayed_handler
            mock_in_app.side_effect = delayed_handler

            # Measure execution time
            start = datetime.now(ZoneInfo("UTC"))
            results = await route_to_handlers(event)
            end = datetime.now(ZoneInfo("UTC"))

            duration_ms = (end - start).total_seconds() * 1000

            # Verify parallel execution
            # With 3 handlers @ 100ms each:
            # - Sequential would be ~300ms
            # - Parallel should be ~100ms (+ small overhead)
            # Allow up to 150ms for overhead
            assert duration_ms < 150, \
                f"Expected parallel execution (~100ms), got {duration_ms:.2f}ms. " \
                f"Sequential execution would be ~300ms!"

            # Verify all succeeded
            assert len(results) == 3
            assert all(r["status"] == "success" for r in results)

    @pytest.mark.asyncio
    async def test_empty_channels_list(self):
        """Test edge case: Event with empty channels list.

        Scenario:
        - ReminderEvent with channels=[]
        - No handlers should be called

        Expected:
        - Empty results list
        - No errors raised
        """
        event = ReminderEvent(
            event_id="test-no-channels",
            task_id=88,
            task_title="No channels task",
            user_id="user-empty",
            due_date="2026-02-24T10:00:00+00:00",
            reminder_type="24h",
            channels=[],  # No channels!
            priority="low"
        )

        with patch('kafka_consumer._send_email_wrapper', new_callable=AsyncMock) as mock_email, \
             patch('kafka_consumer._send_push_wrapper', new_callable=AsyncMock) as mock_push, \
             patch('kafka_consumer._send_in_app_wrapper', new_callable=AsyncMock) as mock_in_app:

            # Execute
            results = await route_to_handlers(event)

            # Verify no handlers called
            assert not mock_email.called
            assert not mock_push.called
            assert not mock_in_app.called

            # Empty results
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_single_channel_enabled(self):
        """Test: User with only one channel enabled (in_app only).

        Scenario:
        - User disabled email and push
        - Only in_app enabled

        Expected:
        - Only 1 result (in_app)
        - In-app delivered successfully
        """
        event = ReminderEvent(
            event_id="test-single-channel",
            task_id=66,
            task_title="Single channel task",
            user_id="user-single",
            due_date="2026-02-25T14:00:00+00:00",
            reminder_type="1h",
            channels=["in_app"],  # Only in_app
            priority="medium"
        )

        mock_in_app_result = {
            "status": "success",
            "sent_at": datetime.now(ZoneInfo("UTC")).isoformat(),
            "error": None
        }

        with patch('kafka_consumer._send_email_wrapper', new_callable=AsyncMock) as mock_email, \
             patch('kafka_consumer._send_push_wrapper', new_callable=AsyncMock) as mock_push, \
             patch('kafka_consumer._send_in_app_wrapper', new_callable=AsyncMock) as mock_in_app:

            mock_in_app.return_value = mock_in_app_result

            # Execute
            results = await route_to_handlers(event)

            # Verify only in_app called
            assert not mock_email.called
            assert not mock_push.called
            assert mock_in_app.called

            # Only 1 result
            assert len(results) == 1
            assert results[0]["channel"] == "in_app"
            assert results[0]["status"] == "success"
