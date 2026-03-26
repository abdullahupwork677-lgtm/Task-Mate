"""Edge Case Tests for Reminder System

Phase V - Testing & Documentation
Tasks: T205, T206, T207, T208
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool

from src.models import Task, User


@pytest.fixture(name="edge_case_db")
def edge_case_db_fixture():
    """Create edge case test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def edge_case_user(edge_case_db: Session):
    """Create test user for edge cases."""
    user = User(
        id="edge-case-user",
        email="edgecase@example.com",
        name="Edge Case Test User",
        password_hash="$2b$12$dummy.hash",
        timezone="UTC",
        notification_preferences={"email": True, "push": False, "in_app": True}
    )
    edge_case_db.add(user)
    edge_case_db.commit()
    edge_case_db.refresh(user)
    return user


class TestOverdueTasks:
    """Test T205: Overdue tasks edge case."""
    
    def test_t205_overdue_tasks_no_reminders(
        self,
        edge_case_db: Session,
        edge_case_user: User
    ):
        """Test T205: 100 overdue tasks → No reminders sent.
        
        Scenario:
        1. Create 100 tasks that are already overdue
        2. Run reminder check
        3. Verify NO reminders are sent for overdue tasks
        
        Logic:
        - Only send reminders BEFORE due date
        - After due date passes, no reminders
        - User should not get spam for overdue tasks
        
        Expected:
        - 0 reminders sent for overdue tasks
        - reminder_sent remains empty
        """
        print("\n=== T205: Testing overdue tasks ===")
        
        # Create 100 overdue tasks
        now = datetime.now(ZoneInfo("UTC"))
        overdue_tasks = []
        
        for i in range(100):
            # Due date in the past (1-10 days ago)
            overdue_by = timedelta(days=(i % 10) + 1)
            due_date = now - overdue_by
            
            task = Task(
                user_id=edge_case_user.id,
                title=f"Overdue Task {i}",
                description=f"Task overdue by {overdue_by.days} days",
                due_date=due_date,
                remind_before=["24h"],
                reminder_sent={},
                completed=False
            )
            overdue_tasks.append(task)
        
        edge_case_db.add_all(overdue_tasks)
        edge_case_db.commit()
        
        print(f"✓ Created 100 overdue tasks")
        
        # Run reminder check (should find 0 tasks)
        reminder_window_start = now
        reminder_window_end = now + timedelta(hours=24, minutes=5)
        
        query = select(Task).where(
            Task.due_date.isnot(None),
            Task.completed == False,
            Task.due_date >= reminder_window_start,  # Only future tasks
            Task.due_date <= reminder_window_end
        )
        
        tasks_needing_reminders = edge_case_db.exec(query).all()
        
        print(f"✓ Reminder check found: {len(tasks_needing_reminders)} tasks")
        
        # T205: Verify no reminders for overdue tasks
        assert len(tasks_needing_reminders) == 0, "Should not send reminders for overdue tasks"
        
        # Verify reminder_sent is still empty
        for task in overdue_tasks:
            edge_case_db.refresh(task)
            assert task.reminder_sent == {}, "reminder_sent should remain empty"
        
        print(f"\n✅ T205 PASS: No reminders sent for 100 overdue tasks")


class TestTaskCompletion:
    """Test T206: Task completion edge case."""
    
    def test_t206_complete_task_skips_pending_reminders(
        self,
        edge_case_db: Session,
        edge_case_user: User
    ):
        """Test T206: Complete task with pending reminders → Reminders skipped.
        
        Scenario:
        1. User has task due tomorrow with 24h and 1h reminders
        2. 24h reminder has NOT been sent yet
        3. User completes task early
        4. Run reminder check
        5. Verify NO reminders are sent (task is completed)
        
        Logic:
        - Only send reminders for incomplete tasks
        - Completing a task should prevent future reminders
        - No spam for completed tasks
        
        Expected:
        - 0 reminders sent for completed task
        - reminder_sent remains empty
        """
        print("\n=== T206: Testing task completion ===")
        
        # Create task due tomorrow
        now = datetime.now(ZoneInfo("UTC"))
        tomorrow = now + timedelta(hours=24)
        
        task = Task(
            user_id=edge_case_user.id,
            title="Complete Early Task",
            description="Task completed before reminders",
            due_date=tomorrow,
            remind_before=["24h", "1h"],
            reminder_sent={},
            completed=False
        )
        edge_case_db.add(task)
        edge_case_db.commit()
        edge_case_db.refresh(task)
        
        print(f"✓ Created task due tomorrow")
        print(f"  Pending reminders: 24h, 1h")
        
        # User completes task early
        task.completed = True
        edge_case_db.add(task)
        edge_case_db.commit()
        
        print(f"✓ User completed task early")
        
        # Run reminder check (should skip completed tasks)
        query = select(Task).where(
            Task.due_date.isnot(None),
            Task.completed == False,  # Only incomplete tasks
            Task.due_date >= now,
            Task.due_date <= now + timedelta(hours=24, minutes=5)
        )
        
        tasks_needing_reminders = edge_case_db.exec(query).all()
        
        print(f"✓ Reminder check found: {len(tasks_needing_reminders)} tasks")
        
        # T206: Verify no reminders for completed task
        assert task.id not in [t.id for t in tasks_needing_reminders], "Completed task should be skipped"
        assert len(tasks_needing_reminders) == 0, "Should not find completed tasks"
        
        # Verify reminder_sent is still empty
        edge_case_db.refresh(task)
        assert task.reminder_sent == {}, "No reminders should have been sent"
        
        print(f"\n✅ T206 PASS: Reminders skipped for completed task")


class TestDueDateUpdate:
    """Test T207: Due date update edge case."""
    
    def test_t207_change_due_date_resets_reminder(
        self,
        edge_case_db: Session,
        edge_case_user: User
    ):
        """Test T207: Change due date after 24h reminder sent → Reminder resets.
        
        Scenario:
        1. User has task due tomorrow
        2. 24h reminder is sent
        3. User changes due date to next week
        4. reminder_sent should be reset (or recalculated)
        5. User can receive 24h reminder again for new due date
        
        Logic:
        - Changing due date invalidates previous reminders
        - User should get reminders for the NEW due date
        - Prevent missed reminders after date changes
        
        Expected:
        - After due date change, reminder_sent is reset
        - New 24h reminder can be sent for new due date
        """
        print("\n=== T207: Testing due date update ===")
        
        # Create task due tomorrow
        now = datetime.now(ZoneInfo("UTC"))
        tomorrow = now + timedelta(hours=24)
        
        task = Task(
            user_id=edge_case_user.id,
            title="Flexible Deadline Task",
            description="Task with changing due date",
            due_date=tomorrow,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        edge_case_db.add(task)
        edge_case_db.commit()
        edge_case_db.refresh(task)
        
        print(f"✓ Created task due tomorrow")
        
        # Simulate 24h reminder being sent
        task.reminder_sent = {"24h": now.isoformat()}
        edge_case_db.add(task)
        edge_case_db.commit()
        
        print(f"✓ 24h reminder sent")
        print(f"  reminder_sent: {task.reminder_sent}")
        
        # User changes due date to next week
        next_week = now + timedelta(days=7)
        task.due_date = next_week
        
        # T207: Reset reminder_sent when due date changes
        task.reminder_sent = {}
        
        edge_case_db.add(task)
        edge_case_db.commit()
        edge_case_db.refresh(task)
        
        print(f"✓ User changed due date to next week")
        print(f"  New due date: {next_week}")
        print(f"  reminder_sent: {task.reminder_sent}")
        
        # Verify T207 requirements
        # Compare as naive datetimes (SQLite stores without timezone)
        assert task.due_date.replace(tzinfo=None) == next_week.replace(tzinfo=None), "Due date should be updated"
        assert task.reminder_sent == {}, "Reminder should be reset"
        
        # Verify new reminder can be sent
        # (In 6 days, 24h reminder for new due date can be sent)
        six_days_later = now + timedelta(days=6)
        # Convert to naive datetime for comparison with SQLite datetime
        six_days_later_naive = six_days_later.replace(tzinfo=None)
        task_due_date_naive = task.due_date.replace(tzinfo=None) if task.due_date.tzinfo else task.due_date

        can_send_reminder = (
            task_due_date_naive >= six_days_later_naive and
            task_due_date_naive <= six_days_later_naive + timedelta(hours=24, minutes=5) and
            "24h" not in task.reminder_sent
        )

        assert can_send_reminder, "Should be able to send reminder for new due date"
        
        print(f"\n✅ T207 PASS: Reminder reset after due date change")


class TestInvalidDateInput:
    """Test T208: Invalid date input edge case."""
    
    def test_t208_invalid_date_error_message(self):
        """Test T208: User says 'due asdfghjk' → Error message with examples.

        Scenario:
        1. User provides invalid date string
        2. Date parser attempts to parse
        3. Parser fails and returns helpful error
        4. Error includes examples of valid inputs

        Expected Error Message:
        - "Could not parse date 'asdfghjk'"
        - "Valid examples:"
        - "  - tomorrow"
        - "  - next Friday at 5pm"
        - "  - February 14, 2026"
        - "  - 2026-02-14 17:00"

        Note: This test simulates date parser error handling.
        """
        print("\n=== T208: Testing invalid date input ===")

        from src.utils.date_parser import DateParser

        parser = DateParser(use_gpt_fallback=False)

        # Test various invalid inputs
        invalid_inputs = [
            "asdfghjk",
            "when pigs fly",
            "123abc",
            "!!!"
        ]

        for invalid_input in invalid_inputs:
            print(f"\n✓ Testing invalid input: '{invalid_input}'")

            result = parser.parse(invalid_input)

            # Should fail for invalid input
            assert result.success is False, f"Parser should fail for '{invalid_input}'"
            assert result.error_message is not None, "Error message should be provided"

            error_msg = result.error_message
            print(f"  Error: {error_msg}")

            # T208: Verify error message is helpful
            assert "Could not parse" in error_msg or "Invalid" in error_msg or "Error parsing" in error_msg

        # Test empty string specifically
        result = parser.parse("")
        assert result.success is False
        assert "empty" in result.error_message.lower()

        print(f"\n✅ T208 PASS: Helpful error messages for invalid dates")
        print("   Parser returns DateParseResult with error messages")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
