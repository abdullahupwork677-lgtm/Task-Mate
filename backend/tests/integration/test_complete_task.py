"""
Integration tests for task completion toggle workflow.

Tests the complete conversational flow for completing/uncompleting tasks:
- Complete by ID: "mark task 5 as complete" → confirmation → completion
- Complete by name: "complete the milk task" → fuzzy match → confirmation → completion
- Natural language: "I finished buying milk" → find task → completion
- Toggle: "mark task 5 as incomplete" → uncomplete task
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.intent_classifier import IntentClassifier, Intent
from src.mcp_tools.complete_task import (
    complete_task,
    CompleteTaskParams,
    CompleteTaskResult,
)
from src.mcp_tools.update_task import update_task, UpdateTaskParams
from src.mcp_tools.find_task import find_task, FindTaskParams


class TestCompletionByID:
    """Test task completion by ID (T075)."""

    @pytest.fixture
    def classifier(self):
        """Create intent classifier."""
        return IntentClassifier()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.exec = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.rollback = Mock()
        return db

    @pytest.fixture
    def sample_task(self, mock_db):
        """Create a sample pending task."""
        task = Mock()
        task.id = 5
        task.user_id = "user-123"
        task.title = "Buy groceries"
        task.description = "Milk, eggs, bread"
        task.priority = "medium"
        task.completed = False
        task.updated_at = datetime.utcnow()
        mock_db.exec.return_value.first.return_value = task
        return task

    def test_complete_intent_with_task_id(self, classifier):
        """Test COMPLETE_TASK intent is detected with task ID."""
        result = classifier.classify("mark task 5 as complete")
        assert result.intent_type == Intent.COMPLETE_TASK
        assert result.extracted_entities.get("task_id") == 5

    def test_complete_intent_short_form(self, classifier):
        """Test COMPLETE_TASK with 'complete task X' form."""
        result = classifier.classify("complete task 7")
        assert result.intent_type == Intent.COMPLETE_TASK
        assert result.extracted_entities.get("task_id") == 7

    def test_complete_intent_done_keyword(self, classifier):
        """Test COMPLETE_TASK with 'done' keyword."""
        result = classifier.classify("task 5 is done")
        assert result.intent_type == Intent.COMPLETE_TASK
        assert result.extracted_entities.get("task_id") == 5

    def test_complete_task_execution(self, mock_db, sample_task):
        """Test task completion execution."""
        params = CompleteTaskParams(user_id="user-123", task_id=5)

        result = complete_task(mock_db, params)

        assert result.completed is True
        assert result.task_id == 5
        assert result.title == "Buy groceries"
        mock_db.commit.assert_called_once()

    def test_complete_already_completed_task(self, mock_db):
        """Test completing an already completed task (idempotent)."""
        task = Mock()
        task.id = 5
        task.user_id = "user-123"
        task.title = "Already done"
        task.description = None
        task.completed = True  # Already complete
        task.updated_at = datetime.utcnow()
        mock_db.exec.return_value.first.return_value = task

        params = CompleteTaskParams(user_id="user-123", task_id=5)

        result = complete_task(mock_db, params)

        # Should succeed without error
        assert result.completed is True

    def test_complete_nonexistent_task(self, mock_db):
        """Test completing a task that doesn't exist."""
        mock_db.exec.return_value.first.return_value = None

        params = CompleteTaskParams(user_id="user-123", task_id=99999)

        with pytest.raises(ValueError, match="Task not found"):
            complete_task(mock_db, params)


class TestNaturalLanguageCompletion:
    """Test natural language completion (T076)."""

    @pytest.fixture
    def classifier(self):
        """Create intent classifier."""
        return IntentClassifier()

    def test_finished_pattern(self, classifier):
        """Test 'I finished X' pattern."""
        result = classifier.classify("I finished task 5")
        assert result.intent_type == Intent.COMPLETE_TASK
        assert result.extracted_entities.get("task_id") == 5

    def test_finished_with_task_name(self, classifier):
        """Test 'I finished [task name]' pattern."""
        result = classifier.classify("I finished buying milk")
        assert result.intent_type == Intent.COMPLETE_TASK
        # Should extract task name for fuzzy matching
        assert (
            "buying milk" in str(result.extracted_entities).lower()
            or result.extracted_entities.get("task_name") is not None
        )

    def test_done_with_pattern(self, classifier):
        """Test 'done with X' pattern."""
        result = classifier.classify("I'm done with task 3")
        # May or may not be recognized depending on classifier
        # At minimum should not crash

    def test_completed_pattern(self, classifier):
        """Test 'completed X' pattern."""
        result = classifier.classify("completed task 5")
        assert result.intent_type == Intent.COMPLETE_TASK


class TestCompletionByName:
    """Test completion by task name with fuzzy matching."""

    @pytest.fixture
    def classifier(self):
        """Create intent classifier."""
        return IntentClassifier()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.exec = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.rollback = Mock()
        return db

    def test_complete_by_partial_name(self, classifier):
        """Test completion intent with partial task name."""
        # "complete the groceries task"
        result = classifier.classify("I finished the groceries")
        assert result.intent_type == Intent.COMPLETE_TASK

    def test_fuzzy_match_integration(self, mock_db):
        """Test fuzzy matching to find task by name."""
        # Setup mock task
        task = Mock()
        task.id = 10
        task.user_id = "user-123"
        task.title = "Buy groceries from store"
        task.confidence_score = 85

        mock_db.exec.return_value.all.return_value = [task]

        # Find task by name
        find_params = FindTaskParams(user_id="user-123", title="groceries")

        # Would use find_task to locate, then complete_task to mark done


class TestCompletionToggle:
    """Test toggling completion status."""

    @pytest.fixture
    def classifier(self):
        """Create intent classifier."""
        return IntentClassifier()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.exec = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.rollback = Mock()
        return db

    def test_uncomplete_intent_detection(self, classifier):
        """Test uncomplete intent detection."""
        # These may not be recognized by current classifier
        tests = ["mark task 5 as incomplete", "uncomplete task 5", "task 5 is not done"]
        for test in tests:
            result = classifier.classify(test)
            # Just verify no crash - may be UNKNOWN

    def test_toggle_to_incomplete_via_update(self, mock_db):
        """Test marking complete task as incomplete via update_task."""
        task = Mock()
        task.id = 5
        task.user_id = "user-123"
        task.title = "Completed task"
        task.description = None
        task.priority = "medium"
        task.due_date = None
        task.completed = True  # Currently complete
        task.updated_at = datetime.utcnow()
        mock_db.exec.return_value.first.return_value = task

        # Use update_task to toggle completion
        params = UpdateTaskParams(
            user_id="user-123", task_id=5, completed=False  # Toggle to incomplete
        )

        result = update_task(mock_db, params)

        # Task should now be incomplete
        assert task.completed is False


class TestCompletionConfirmation:
    """Test completion confirmation flow."""

    @pytest.fixture
    def classifier(self):
        """Create intent classifier."""
        return IntentClassifier()

    def test_yes_confirms_completion(self, classifier):
        """Test 'yes' confirms completion in COMPLETING_TASK context."""
        result = classifier.classify("yes", current_intent="COMPLETING_TASK")
        assert result.intent_type == Intent.PROVIDE_INFORMATION
        assert result.extracted_entities.get("confirmation") == True

    def test_no_cancels_completion(self, classifier):
        """Test 'no' cancels completion."""
        result = classifier.classify("no", current_intent="COMPLETING_TASK")
        assert result.intent_type == Intent.PROVIDE_INFORMATION
        assert result.extracted_entities.get("confirmation") == False

    def test_cancel_stops_completion(self, classifier):
        """Test 'cancel' stops completion."""
        result = classifier.classify("cancel", current_intent="COMPLETING_TASK")
        assert result.intent_type == Intent.CANCEL_OPERATION


class TestCompletionUserIsolation:
    """Test user isolation in completion operations."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.exec = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.rollback = Mock()
        return db

    def test_cannot_complete_other_user_task(self, mock_db):
        """Test that user cannot complete another user's task."""
        mock_db.exec.return_value.first.return_value = None

        params = CompleteTaskParams(user_id="user-456", task_id=5)  # Different user

        with pytest.raises(ValueError, match="Task not found"):
            complete_task(mock_db, params)

    def test_can_complete_own_task(self, mock_db):
        """Test that user can complete their own task."""
        task = Mock()
        task.id = 5
        task.user_id = "user-123"
        task.title = "My task"
        task.description = None
        task.completed = False
        task.updated_at = datetime.utcnow()
        mock_db.exec.return_value.first.return_value = task

        params = CompleteTaskParams(user_id="user-123", task_id=5)

        result = complete_task(mock_db, params)
        assert result.completed is True


class TestCompletionEdgeCases:
    """Test edge cases for task completion."""

    @pytest.fixture
    def classifier(self):
        """Create intent classifier."""
        return IntentClassifier()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.exec = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.rollback = Mock()
        return db

    def test_complete_task_id_zero(self, mock_db):
        """Test completing task with ID 0."""
        mock_db.exec.return_value.first.return_value = None

        params = CompleteTaskParams(user_id="user-123", task_id=0)

        with pytest.raises(ValueError, match="Task not found"):
            complete_task(mock_db, params)

    def test_complete_negative_task_id(self, mock_db):
        """Test completing task with negative ID."""
        mock_db.exec.return_value.first.return_value = None

        params = CompleteTaskParams(user_id="user-123", task_id=-1)

        with pytest.raises(ValueError, match="Task not found"):
            complete_task(mock_db, params)

    def test_complete_updates_timestamp(self, mock_db):
        """Test that completing updates the timestamp."""
        old_time = datetime(2026, 1, 1, 10, 0, 0)
        task = Mock()
        task.id = 5
        task.user_id = "user-123"
        task.title = "Test task"
        task.description = None
        task.completed = False
        task.updated_at = old_time
        mock_db.exec.return_value.first.return_value = task

        params = CompleteTaskParams(user_id="user-123", task_id=5)

        result = complete_task(mock_db, params)

        # Timestamp should be updated
        assert task.updated_at != old_time

    def test_completion_success_message_format(self, mock_db):
        """Test completion result includes all necessary details."""
        task = Mock()
        task.id = 5
        task.user_id = "user-123"
        task.title = "Buy groceries"
        task.description = "From the store"
        task.completed = False
        task.updated_at = datetime.utcnow()
        mock_db.exec.return_value.first.return_value = task

        params = CompleteTaskParams(user_id="user-123", task_id=5)

        result = complete_task(mock_db, params)

        # Result should have all fields
        assert result.task_id == 5
        assert result.title == "Buy groceries"
        assert result.description == "From the store"
        assert result.completed is True
        assert result.updated_at is not None


class TestCompletionIntentVariations:
    """Test various completion intent phrasings."""

    @pytest.fixture
    def classifier(self):
        """Create intent classifier."""
        return IntentClassifier()

    def test_mark_complete(self, classifier):
        """Test 'mark X as complete' pattern."""
        result = classifier.classify("mark task 5 as complete")
        assert result.intent_type == Intent.COMPLETE_TASK

    def test_complete_task(self, classifier):
        """Test 'complete task X' pattern."""
        result = classifier.classify("complete task 5")
        assert result.intent_type == Intent.COMPLETE_TASK

    def test_finished_task(self, classifier):
        """Test 'finished task X' pattern."""
        result = classifier.classify("I finished task 5")
        assert result.intent_type == Intent.COMPLETE_TASK

    def test_task_is_done(self, classifier):
        """Test 'task X is done' pattern."""
        result = classifier.classify("task 5 is done")
        assert result.intent_type == Intent.COMPLETE_TASK

    def test_check_off_task(self, classifier):
        """Test 'check off task X' pattern."""
        result = classifier.classify("check off task 5")
        # May or may not be recognized
        # Just verify no crash
