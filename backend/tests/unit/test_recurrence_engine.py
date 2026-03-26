"""Unit Tests for Recurrence Engine

Tests the recurrence calculation logic in isolation.
Following TDD approach - tests written FIRST before implementation.
"""

import pytest
from datetime import datetime, timedelta
from src.services.recurrence_engine import (
    calculate_next_due_date,
    parse_recurrence_pattern,
    validate_recurrence_pattern,
)


class TestCalculateNextDueDate:
    """Test suite for calculate_next_due_date function."""

    def test_daily_recurrence(self):
        """Test daily recurrence adds 1 day."""
        current_due = datetime(2026, 2, 9, 10, 0, 0)
        next_due = calculate_next_due_date(current_due, "daily")
        assert next_due == datetime(2026, 2, 10, 10, 0, 0)

    def test_weekly_recurrence(self):
        """Test weekly recurrence adds 7 days."""
        current_due = datetime(2026, 2, 9, 10, 0, 0)
        next_due = calculate_next_due_date(current_due, "weekly")
        assert next_due == datetime(2026, 2, 16, 10, 0, 0)

    def test_monthly_recurrence(self):
        """Test monthly recurrence adds 1 month."""
        current_due = datetime(2026, 2, 9, 10, 0, 0)
        next_due = calculate_next_due_date(current_due, "monthly")
        assert next_due == datetime(2026, 3, 9, 10, 0, 0)

    def test_custom_interval_every_3_days(self):
        """Test custom interval 'every 3 days'."""
        current_due = datetime(2026, 2, 9, 10, 0, 0)
        next_due = calculate_next_due_date(current_due, "every 3 days")
        assert next_due == datetime(2026, 2, 12, 10, 0, 0)

    def test_yearly_recurrence(self):
        """Test yearly recurrence adds 1 year."""
        current_due = datetime(2026, 2, 9, 10, 0, 0)
        next_due = calculate_next_due_date(current_due, "yearly")
        assert next_due == datetime(2027, 2, 9, 10, 0, 0)

    def test_custom_interval_every_2_weeks(self):
        """Test custom interval 'every 2 weeks'."""
        current_due = datetime(2026, 2, 9, 10, 0, 0)
        next_due = calculate_next_due_date(current_due, "every 2 weeks")
        assert next_due == datetime(2026, 2, 23, 10, 0, 0)

    def test_month_end_handling_feb_31(self):
        """Test Feb 31 becomes Feb 28/29 (month-end edge case)."""
        current_due = datetime(2026, 1, 31, 10, 0, 0)
        next_due = calculate_next_due_date(current_due, "monthly")
        # February 2026 has 28 days (not a leap year)
        assert next_due == datetime(2026, 2, 28, 10, 0, 0)

    def test_leap_year_handling(self):
        """Test leap year handling (Feb 29 in leap year)."""
        current_due = datetime(2024, 1, 31, 10, 0, 0)  # 2024 is a leap year
        next_due = calculate_next_due_date(current_due, "monthly")
        # February 2024 has 29 days (leap year)
        assert next_due == datetime(2024, 2, 29, 10, 0, 0)

    def test_recurrence_end_date_reached(self):
        """Test recurrence returns None when end date reached."""
        current_due = datetime(2026, 12, 25, 10, 0, 0)
        end_date = datetime(2026, 12, 31, 23, 59, 59)
        next_due = calculate_next_due_date(current_due, "weekly", end_date)
        # Next occurrence would be Jan 1, 2027, but end_date is Dec 31, 2026
        assert next_due is None

    def test_invalid_pattern_raises_error(self):
        """Test invalid pattern raises ValueError."""
        current_due = datetime(2026, 2, 9, 10, 0, 0)
        with pytest.raises(ValueError):
            calculate_next_due_date(current_due, "every century")


class TestParseRecurrencePattern:
    """Test suite for parse_recurrence_pattern function."""

    def test_parse_daily(self):
        """Test parsing 'daily' pattern."""
        freq, interval = parse_recurrence_pattern("daily")
        assert freq == "daily"
        assert interval == 1

    def test_parse_weekly(self):
        """Test parsing 'weekly' pattern."""
        freq, interval = parse_recurrence_pattern("weekly")
        assert freq == "weekly"
        assert interval == 1

    def test_parse_custom_every_3_days(self):
        """Test parsing 'every 3 days' pattern."""
        freq, interval = parse_recurrence_pattern("every 3 days")
        assert freq == "days"
        assert interval == 3

    def test_parse_custom_every_2_weeks(self):
        """Test parsing 'every 2 weeks' pattern."""
        freq, interval = parse_recurrence_pattern("every 2 weeks")
        assert freq == "weeks"
        assert interval == 2


class TestValidateRecurrencePattern:
    """Test suite for validate_recurrence_pattern function."""

    def test_valid_daily(self):
        """Test 'daily' is valid."""
        assert validate_recurrence_pattern("daily") is True

    def test_valid_weekly(self):
        """Test 'weekly' is valid."""
        assert validate_recurrence_pattern("weekly") is True

    def test_valid_monthly(self):
        """Test 'monthly' is valid."""
        assert validate_recurrence_pattern("monthly") is True

    def test_valid_custom_every_3_days(self):
        """Test 'every 3 days' is valid."""
        assert validate_recurrence_pattern("every 3 days") is True

    def test_invalid_century(self):
        """Test 'every century' is invalid."""
        assert validate_recurrence_pattern("every century") is False

    def test_invalid_negative_interval(self):
        """Test negative interval is invalid."""
        assert validate_recurrence_pattern("every -5 days") is False
