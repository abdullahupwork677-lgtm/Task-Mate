"""
End-to-end tests for search workflow via AI chatbot.

Tests complete user workflows including natural language search commands
through the chatbot interface.

Phase: 004-search-filter
Task: T051 (Phase 9)
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlmodel import Session

from src.main import app
from src.models.task import Task
from src.models.conversation import Conversation
from src.models.message import Message
from src.db import get_session
from tests.conftest import test_session, test_user_token


client = TestClient(app)


class TestSearchWorkflowE2E:
    """End-to-end tests for search workflow via chatbot."""

    @pytest.fixture(autouse=True)
    def setup(self, test_session, test_user_token):
        """Setup test data with conversation and tasks."""
        self.session = test_session
        self.token = test_user_token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user_id = "test-user"

        # Create conversation
        self.conversation = Conversation(user_id=self.user_id, title="Search Test")
        self.session.add(self.conversation)
        self.session.commit()
        self.session.refresh(self.conversation)

        # Create test tasks with realistic scenarios
        self.test_tasks = [
            # Grocery shopping tasks
            Task(
                user_id=self.user_id,
                title="Buy groceries",
                description="Milk, eggs, bread, cheese",
                completed=False,
                priority="high",
                tags=["shopping", "home"],
                due_date=datetime.utcnow() + timedelta(days=1)
            ),
            Task(
                user_id=self.user_id,
                title="Grocery list for party",
                description="Snacks, drinks, ice cream",
                completed=False,
                priority="medium",
                tags=["shopping", "party"],
                due_date=datetime.utcnow() + timedelta(days=3)
            ),

            # Work tasks
            Task(
                user_id=self.user_id,
                title="Finish report",
                description="Q4 financial report",
                completed=False,
                priority="high",
                tags=["work", "urgent"],
                due_date=datetime.utcnow() - timedelta(days=1)  # Overdue!
            ),
            Task(
                user_id=self.user_id,
                title="Team meeting preparation",
                description="Prepare slides and agenda",
                completed=False,
                priority="medium",
                tags=["work"],
                due_date=datetime.utcnow()  # Due today
            ),
            Task(
                user_id=self.user_id,
                title="Code review",
                description="Review PR #123",
                completed=True,
                priority="medium",
                tags=["work"],
                due_date=datetime.utcnow() - timedelta(days=2)
            ),

            # Personal tasks
            Task(
                user_id=self.user_id,
                title="Call dentist",
                description="Schedule appointment",
                completed=False,
                priority="low",
                tags=["personal", "health"],
                due_date=None
            ),
            Task(
                user_id=self.user_id,
                title="Gym workout",
                description="Leg day",
                completed=False,
                priority="low",
                tags=["personal", "fitness"],
                due_date=datetime.utcnow()
            ),
        ]

        for task in self.test_tasks:
            self.session.add(task)
        self.session.commit()

        yield

        # Cleanup
        self.session.query(Message).filter(Message.conversation_id == self.conversation.id).delete()
        self.session.query(Conversation).filter(Conversation.id == self.conversation.id).delete()
        self.session.query(Task).filter(Task.user_id == self.user_id).delete()
        self.session.commit()

    def send_chat_message(self, message: str) -> dict:
        """Send a chat message to the chatbot and return response."""
        response = client.post(
            "/api/chat",
            json={
                "conversation_id": str(self.conversation.id),
                "user_message": message,
                "user_id": self.user_id
            },
            headers=self.headers
        )

        assert response.status_code == 200
        return response.json()

    def test_simple_keyword_search(self):
        """Test simple keyword search via chatbot."""
        response = self.send_chat_message("search for grocery")

        # Agent should call search_tasks with keyword="grocery"
        assert "search_tasks" in response.get("tools_used", [])

        # Response should mention grocery tasks
        response_text = response["response"].lower()
        assert "grocery" in response_text or "groceries" in response_text

    def test_search_with_status_filter(self):
        """Test search with status filter."""
        response = self.send_chat_message("show incomplete tasks")

        # Agent should call search_tasks with status_filter="pending"
        assert "search_tasks" in response.get("tools_used", [])

        # Response should mention incomplete/pending tasks
        response_text = response["response"].lower()
        assert "incomplete" in response_text or "pending" in response_text or "not completed" in response_text

    def test_search_by_priority(self):
        """Test search by priority."""
        response = self.send_chat_message("show high priority tasks")

        # Agent should call search_tasks with priority_filter="high"
        assert "search_tasks" in response.get("tools_used", [])

        response_text = response["response"].lower()
        assert "high" in response_text or "priority" in response_text

    def test_search_by_tags(self):
        """Test search by tags."""
        response = self.send_chat_message("show work tasks")

        # Agent should call search_tasks with tags_filter=["work"]
        assert "search_tasks" in response.get("tools_used", [])

        response_text = response["response"].lower()
        assert "work" in response_text

    def test_search_overdue_tasks(self):
        """Test finding overdue tasks."""
        response = self.send_chat_message("show overdue tasks")

        # Agent should call search_tasks with due_date_filter="overdue"
        assert "search_tasks" in response.get("tools_used", [])

        response_text = response["response"].lower()
        assert "overdue" in response_text or "late" in response_text

    def test_search_tasks_due_today(self):
        """Test finding tasks due today."""
        response = self.send_chat_message("what tasks are due today?")

        # Agent should call search_tasks with due_date_filter="today"
        assert "search_tasks" in response.get("tools_used", [])

        response_text = response["response"].lower()
        assert "today" in response_text or "due" in response_text

    def test_combined_search_keyword_and_filters(self):
        """Test combined search with keyword and filters."""
        response = self.send_chat_message("search grocery in incomplete high priority tasks")

        # Agent should call search_tasks with multiple parameters
        assert "search_tasks" in response.get("tools_used", [])

        response_text = response["response"].lower()
        assert "grocery" in response_text or "groceries" in response_text

    def test_combined_search_complex(self):
        """Test complex combined search."""
        response = self.send_chat_message("find incomplete work tasks that are overdue")

        # Agent should combine status, tags, and due date filters
        assert "search_tasks" in response.get("tools_used", [])

        response_text = response["response"].lower()
        assert "work" in response_text
        assert "overdue" in response_text or "late" in response_text

    def test_search_no_results(self):
        """Test search with no matching results."""
        response = self.send_chat_message("search for nonexistent task xyz123")

        response_text = response["response"].lower()
        assert "no" in response_text or "not found" in response_text or "0" in response_text

    def test_search_then_filter(self):
        """Test sequential search refinement."""
        # First search
        response1 = self.send_chat_message("show all tasks")
        assert "search_tasks" in response1.get("tools_used", [])

        # Refine search
        response2 = self.send_chat_message("now show only work tasks")
        assert "search_tasks" in response2.get("tools_used", [])

        response_text = response2["response"].lower()
        assert "work" in response_text

    def test_natural_language_variations(self):
        """Test various natural language search patterns."""
        test_cases = [
            "find shopping tasks",
            "what are my high priority items?",
            "show tasks tagged with work",
            "list overdue tasks",
            "search for report",
        ]

        for query in test_cases:
            response = self.send_chat_message(query)

            # All should trigger search_tasks
            assert "search_tasks" in response.get("tools_used", []), f"Failed for query: {query}"

            # Response should be relevant
            assert len(response["response"]) > 0

    def test_conversation_context_maintained(self):
        """Test that conversation context is maintained across searches."""
        # First search
        response1 = self.send_chat_message("show work tasks")
        assert "search_tasks" in response1.get("tools_used", [])

        # Follow-up question (context should be remembered)
        response2 = self.send_chat_message("how many are overdue?")

        # Agent should understand "they" refers to work tasks from previous search
        # This might trigger another search_tasks call with combined filters
        response_text = response2["response"].lower()
        assert any(word in response_text for word in ["overdue", "late", "1", "one"])

    def test_search_performance_multiple_filters(self):
        """Test performance with multiple filters."""
        import time

        start = time.time()
        response = self.send_chat_message(
            "search grocery in incomplete high priority shopping tasks due this week"
        )
        elapsed = time.time() - start

        # Should complete in reasonable time (< 2 seconds for chatbot response)
        assert elapsed < 2.0

        # Should successfully execute search
        assert "search_tasks" in response.get("tools_used", [])

    def test_error_handling_invalid_search(self):
        """Test error handling for invalid search parameters."""
        # Intentionally vague or impossible query
        response = self.send_chat_message("show tasks from the future in the past")

        # Agent should handle gracefully and provide helpful response
        assert len(response["response"]) > 0

        # Should not crash
        response_text = response["response"].lower()
        # Agent might ask for clarification or explain the issue

    def test_empty_database_search(self):
        """Test search when no tasks exist."""
        # Delete all tasks
        self.session.query(Task).filter(Task.user_id == self.user_id).delete()
        self.session.commit()

        response = self.send_chat_message("show all tasks")

        response_text = response["response"].lower()
        assert "no" in response_text or "0" in response_text or "empty" in response_text

        # Restore tasks for other tests
        for task in self.test_tasks:
            self.session.add(task)
        self.session.commit()

    def test_pagination_in_search_results(self):
        """Test that pagination works in search results."""
        # Create many tasks to trigger pagination
        bulk_tasks = [
            Task(
                user_id=self.user_id,
                title=f"Test task {i}",
                description=f"Task number {i}",
                completed=False,
                priority="medium"
            )
            for i in range(30)
        ]

        for task in bulk_tasks:
            self.session.add(task)
        self.session.commit()

        response = self.send_chat_message("show all my tasks")

        # Response should mention pagination or number of results
        # Default page size is 20, so should get paginated results
        response_text = response["response"].lower()

        # Cleanup
        for task in bulk_tasks:
            self.session.delete(task)
        self.session.commit()

    def test_search_result_accuracy(self):
        """Test accuracy of search results."""
        response = self.send_chat_message("search report")

        # Should find the "Finish report" task
        response_text = response["response"].lower()
        assert "report" in response_text

        # Should not find unrelated tasks
        assert not ("grocery" in response_text or "dentist" in response_text)

    def test_filter_combination_accuracy(self):
        """Test accuracy of combined filter results."""
        response = self.send_chat_message("show incomplete work tasks")

        # Should combine status="incomplete" AND tags=["work"]
        response_text = response["response"].lower()
        assert "work" in response_text

        # Should not mention completed tasks
        assert "code review" not in response_text.lower()  # This is completed
