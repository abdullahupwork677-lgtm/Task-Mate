"""
Integration tests for search and filter API.

Tests all filter combinations and edge cases for the task search functionality.

Phase: 004-search-filter
Task: T050 (Phase 9)
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlmodel import Session

from src.main import app
from src.models.task import Task
from src.db import get_session
from tests.conftest import test_session, test_user_token


client = TestClient(app)


class TestSearchAPI:
    """Integration tests for search and filter endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, test_session, test_user_token):
        """Setup test data."""
        self.session = test_session
        self.token = test_user_token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user_id = "test-user"

        # Create test tasks with different attributes
        self.test_tasks = [
            # Keyword search tests
            Task(user_id=self.user_id, title="Buy groceries", description="Milk, eggs, bread", completed=False),
            Task(user_id=self.user_id, title="Grocery shopping list", description="Weekly groceries", completed=False),
            Task(user_id=self.user_id, title="Call plumber", description="Fix kitchen sink", completed=False),

            # Status filter tests
            Task(user_id=self.user_id, title="Completed task", description="Done", completed=True),
            Task(user_id=self.user_id, title="Pending task", description="Not done", completed=False),

            # Priority filter tests
            Task(user_id=self.user_id, title="High priority work", description="Urgent", priority="high", completed=False),
            Task(user_id=self.user_id, title="Medium priority task", description="Normal", priority="medium", completed=False),
            Task(user_id=self.user_id, title="Low priority task", description="Later", priority="low", completed=False),

            # Tags filter tests
            Task(user_id=self.user_id, title="Work task", description="Office work", tags=["work"], completed=False),
            Task(user_id=self.user_id, title="Personal task", description="Home", tags=["personal"], completed=False),
            Task(user_id=self.user_id, title="Urgent work", description="Important", tags=["work", "urgent"], completed=False),

            # Due date filter tests
            Task(user_id=self.user_id, title="Overdue task", description="Late", due_date=datetime.utcnow() - timedelta(days=2), completed=False),
            Task(user_id=self.user_id, title="Due today", description="Today", due_date=datetime.utcnow(), completed=False),
            Task(user_id=self.user_id, title="Due this week", description="Week", due_date=datetime.utcnow() + timedelta(days=3), completed=False),
            Task(user_id=self.user_id, title="Due this month", description="Month", due_date=datetime.utcnow() + timedelta(days=15), completed=False),
            Task(user_id=self.user_id, title="No due date", description="Anytime", due_date=None, completed=False),
        ]

        # Add all tasks to database
        for task in self.test_tasks:
            self.session.add(task)
        self.session.commit()

        yield

        # Cleanup
        self.session.query(Task).delete()
        self.session.commit()

    def test_keyword_search(self):
        """Test keyword search functionality."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&keyword=grocery",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find 2 tasks with "grocery" in title or description
        assert data["total_count"] == 2
        assert len(data["tasks"]) == 2

        # Verify keyword match
        titles = [task["title"] for task in data["tasks"]]
        assert any("groceries" in title.lower() for title in titles)
        assert any("grocery" in title.lower() for title in titles)

    def test_keyword_search_case_insensitive(self):
        """Test keyword search is case-insensitive."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&keyword=GROCERY",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2

    def test_status_filter_completed(self):
        """Test filtering by completed status."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&status_filter=completed",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find only completed tasks
        assert all(task["completed"] for task in data["tasks"])

    def test_status_filter_incomplete(self):
        """Test filtering by incomplete status."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&status_filter=incomplete",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find only incomplete tasks
        assert all(not task["completed"] for task in data["tasks"])

    def test_priority_filter_high(self):
        """Test filtering by high priority."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&priority_filter=high",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find only high priority tasks
        assert all(task["priority"] == "high" for task in data["tasks"])

    def test_tags_filter_single(self):
        """Test filtering by a single tag."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&tags_filter=work",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find tasks with "work" tag
        assert all("work" in task.get("tags", []) for task in data["tasks"])

    def test_tags_filter_multiple_or_logic(self):
        """Test filtering by multiple tags with OR logic."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&tags_filter=work,personal",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find tasks with EITHER "work" OR "personal" tag
        for task in data["tasks"]:
            tags = task.get("tags", [])
            assert "work" in tags or "personal" in tags

    def test_due_date_filter_overdue(self):
        """Test filtering by overdue tasks."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&due_date_filter=overdue",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find overdue tasks
        now = datetime.utcnow()
        for task in data["tasks"]:
            if task.get("due_date"):
                due_date = datetime.fromisoformat(task["due_date"].replace("Z", "+00:00"))
                assert due_date < now

    def test_due_date_filter_no_due_date(self):
        """Test filtering tasks with no due date."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&due_date_filter=no_due_date",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find tasks with no due date
        assert all(task.get("due_date") is None for task in data["tasks"])

    def test_combined_filters_keyword_and_status(self):
        """Test combining keyword search with status filter."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&keyword=task&status_filter=incomplete",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find incomplete tasks matching "task"
        for task in data["tasks"]:
            assert not task["completed"]
            title_desc = f"{task['title']} {task.get('description', '')}".lower()
            assert "task" in title_desc

    def test_combined_filters_priority_and_tags(self):
        """Test combining priority and tags filters."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&priority_filter=high&tags_filter=work",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find high priority work tasks
        for task in data["tasks"]:
            assert task["priority"] == "high"
            assert "work" in task.get("tags", [])

    def test_combined_filters_all(self):
        """Test combining all filters together."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&keyword=work&status_filter=incomplete&priority_filter=high&tags_filter=work",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should find tasks matching ALL criteria
        for task in data["tasks"]:
            assert not task["completed"]
            assert task["priority"] == "high"
            assert "work" in task.get("tags", [])
            title_desc = f"{task['title']} {task.get('description', '')}".lower()
            assert "work" in title_desc

    def test_pagination_first_page(self):
        """Test pagination first page."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&page=1&page_size=5",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should return first 5 tasks
        assert len(data["tasks"]) <= 5
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["has_prev"] == False

    def test_pagination_second_page(self):
        """Test pagination second page."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&page=2&page_size=5",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["page"] == 2
        assert data["pagination"]["has_prev"] == True

    def test_applied_filters_summary(self):
        """Test applied filters summary generation."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&keyword=grocery&status_filter=incomplete&priority_filter=high",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should have applied filters summary
        assert "applied_filters" in data
        assert "summary" in data["applied_filters"]

        # Summary should mention filters
        summary = data["applied_filters"]["summary"].lower()
        assert "grocery" in summary or "matching" in summary
        assert "incomplete" in summary or "pending" in summary
        assert "high" in summary

    def test_user_isolation(self):
        """Test that users can only see their own tasks."""
        # Create task for different user
        other_task = Task(
            user_id="other-user",
            title="Other user task",
            description="Should not appear",
            completed=False
        )
        self.session.add(other_task)
        self.session.commit()

        response = client.get(
            f"/api/search?user_id={self.user_id}",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should not find other user's task
        titles = [task["title"] for task in data["tasks"]]
        assert "Other user task" not in titles

        # Cleanup
        self.session.delete(other_task)
        self.session.commit()

    def test_empty_results(self):
        """Test search with no matching results."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&keyword=nonexistent",
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 0
        assert len(data["tasks"]) == 0
        assert "applied_filters" in data

    def test_invalid_status_filter(self):
        """Test invalid status filter value."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&status_filter=invalid",
            headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_invalid_priority_filter(self):
        """Test invalid priority filter value."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&priority_filter=invalid",
            headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_invalid_page_number(self):
        """Test invalid page number (< 1)."""
        response = client.get(
            f"/api/search?user_id={self.user_id}&page=0",
            headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_performance_large_result_set(self):
        """Test performance with large result set."""
        import time

        # Create 100 additional tasks
        bulk_tasks = [
            Task(
                user_id=self.user_id,
                title=f"Task {i}",
                description=f"Description {i}",
                completed=i % 2 == 0,
                priority=["high", "medium", "low"][i % 3]
            )
            for i in range(100)
        ]

        for task in bulk_tasks:
            self.session.add(task)
        self.session.commit()

        # Measure search time
        start = time.time()
        response = client.get(
            f"/api/search?user_id={self.user_id}",
            headers=self.headers
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.5  # Should complete in < 500ms

        # Cleanup
        for task in bulk_tasks:
            self.session.delete(task)
        self.session.commit()
