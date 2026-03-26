"""Unit Tests for Recurrence Cancellation

Tests the cancellation functionality (pattern="none") of set_recurring tool.
Following TDD approach - tests written FIRST before implementation.
"""

import pytest
from src.mcp_tools.set_recurring import set_recurring, _validate_pattern


class TestRecurrenceCancellation:
    """Test suite for cancelling recurrence."""

    def test_validate_pattern_none_is_valid(self):
        """Test that pattern='none' is a valid pattern for cancellation."""
        # Should not raise ValueError
        _validate_pattern("none")

    def test_pattern_none_case_insensitive(self):
        """Test that pattern='NONE' and 'None' are also valid."""
        _validate_pattern("NONE")
        _validate_pattern("None")

    @pytest.mark.asyncio
    async def test_cancel_recurring_with_pattern_none(self):
        """Test cancelling recurrence by setting pattern to 'none'."""
        # This test verifies the tool accepts pattern="none"
        # Actual database testing is in integration tests
        # Here we just verify the validation passes
        try:
            _validate_pattern("none")
            assert True
        except ValueError:
            pytest.fail("pattern='none' should be valid for cancellation")
