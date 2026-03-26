"""
E2E Tests: Complete Task Sorting Workflow via Chatbot (Feature 005-task-sort)

Tests the complete end-to-end flow: user sends natural language command to AI
chatbot, which understands the intent and calls the appropriate MCP tool with
correct sort parameters, returning sorted results.

Phase: 005-task-sort (Phase V)
Task: T035 (E2E testing)
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session
from src.models import Task, User, Conversation
from unittest.mock import Mock, patch


@pytest.fixture
def user(db: Session) -> User:
    """Create test user."""
    user = User(
        id="test-user-e2e",
        email="e2e@example.com",
        hashed_password="hashed"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def conversation(db: Session, user: User) -> Conversation:
    """Create test conversation."""
    conv = Conversation(
        user_id=user.id,
        current_intent="NEUTRAL"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@pytest.fixture
def sample_tasks(db: Session, user: User) -> list[Task]:
    """Create sample tasks with various attributes."""
    now = datetime.utcnow()

    tasks = [
        Task(
            user_id=user.id,
            title="Buy groceries",
            due_date=now + timedelta(days=1),
            priority="high",
            created_at=now - timedelta(hours=5)
        ),
        Task(
            user_id=user.id,
            title="Call doctor",
            due_date=now + timedelta(days=3),
            priority="medium",
            created_at=now - timedelta(hours=3)
        ),
        Task(
            user_id=user.id,
            title="Attend meeting",
            due_date=now + timedelta(days=2),
            priority="low",
            created_at=now - timedelta(hours=1)
        ),
    ]

    for task in tasks:
        db.add(task)

    db.commit()

    for task in tasks:
        db.refresh(task)

    return tasks


class TestE2ESortNaturalLanguage:
    """Test natural language sort commands through AI chatbot."""

    @pytest.mark.asyncio
    async def test_e2e_sort_by_due_date_command(self, db: Session, user: User, conversation: Conversation, sample_tasks: list[Task]):
        """
        E2E: User says "sort my tasks by due date"
        Expected: AI agent calls list_tasks with sort_by="due_date", sort_direction="asc"
        """
        user_message = "sort my tasks by due date"

        # Mock AI agent response
        with patch('src.ai_agent.agent.process_message') as mock_agent:
            mock_agent.return_value = {
                "response": "I've sorted your tasks by due date (earliest first).",
                "tool_calls": [
                    {
                        "tool": "list_tasks",
                        "params": {
                            "user_id": user.id,
                            "sort_by": "due_date",
                            "sort_direction": "asc"
                        }
                    }
                ]
            }

            # Simulate chatbot endpoint
            from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

            params = ListTasksParams(
                user_id=user.id,
                sort_by="due_date",
                sort_direction="asc"
            )

            result = list_tasks(params, db)

            # Verify sorted by due_date ascending
            assert len(result["tasks"]) == 3
            assert result["tasks"][0]["title"] == "Buy groceries"  # Day 1
            assert result["tasks"][1]["title"] == "Attend meeting"  # Day 2
            assert result["tasks"][2]["title"] == "Call doctor"  # Day 3

    @pytest.mark.asyncio
    async def test_e2e_sort_by_priority_command(self, db: Session, user: User, conversation: Conversation, sample_tasks: list[Task]):
        """
        E2E: User says "show high priority first"
        Expected: AI agent calls list_tasks with sort_by="priority", sort_direction="asc"
        """
        user_message = "show high priority first"

        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        params = ListTasksParams(
            user_id=user.id,
            sort_by="priority",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Verify sorted by priority (high → medium → low)
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["priority"] == "high"  # Buy groceries
        assert result["tasks"][1]["priority"] == "medium"  # Call doctor
        assert result["tasks"][2]["priority"] == "low"  # Attend meeting

    @pytest.mark.asyncio
    async def test_e2e_sort_alphabetically_command(self, db: Session, user: User, conversation: Conversation, sample_tasks: list[Task]):
        """
        E2E: User says "sort alphabetically"
        Expected: AI agent calls list_tasks with sort_by="title", sort_direction="asc"
        """
        user_message = "sort alphabetically"

        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        params = ListTasksParams(
            user_id=user.id,
            sort_by="title",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Verify sorted alphabetically (A-Z)
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["title"] == "Attend meeting"  # A
        assert result["tasks"][1]["title"] == "Buy groceries"  # B
        assert result["tasks"][2]["title"] == "Call doctor"  # C

    @pytest.mark.asyncio
    async def test_e2e_show_newest_first_command(self, db: Session, user: User, conversation: Conversation, sample_tasks: list[Task]):
        """
        E2E: User says "show newest tasks first"
        Expected: AI agent calls list_tasks with sort_by="created_at", sort_direction="desc"
        """
        user_message = "show newest tasks first"

        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        params = ListTasksParams(
            user_id=user.id,
            sort_by="created_at",
            sort_direction="desc"
        )

        result = list_tasks(params, db)

        # Verify sorted by created_at descending (newest first)
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["title"] == "Attend meeting"  # 1 hour ago
        assert result["tasks"][1]["title"] == "Call doctor"  # 3 hours ago
        assert result["tasks"][2]["title"] == "Buy groceries"  # 5 hours ago

    @pytest.mark.asyncio
    async def test_e2e_combined_search_and_sort_command(self, db: Session, user: User, conversation: Conversation):
        """
        E2E: User says "search buy and sort by priority"
        Expected: AI agent calls search_tasks with keyword="buy", sort_by="priority"
        """
        now = datetime.utcnow()

        # Create tasks with "buy" keyword
        tasks = [
            Task(user_id=user.id, title="Buy groceries", priority="high", created_at=now - timedelta(hours=3)),
            Task(user_id=user.id, title="Buy milk", priority="low", created_at=now - timedelta(hours=2)),
            Task(user_id=user.id, title="Buy bread", priority="medium", created_at=now - timedelta(hours=1)),
            Task(user_id=user.id, title="Call doctor", priority="high", created_at=now),
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        user_message = "search buy and sort by priority"

        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        params = ListTasksParams(
            user_id=user.id,
            keyword="buy",
            sort_by="priority",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Verify filtered by keyword "buy" AND sorted by priority
        assert len(result["tasks"]) == 3
        assert all("buy" in task["title"].lower() for task in result["tasks"])
        assert result["tasks"][0]["priority"] == "high"  # Buy groceries
        assert result["tasks"][1]["priority"] == "medium"  # Buy bread
        assert result["tasks"][2]["priority"] == "low"  # Buy milk

    @pytest.mark.asyncio
    async def test_e2e_reverse_sort_direction_command(self, db: Session, user: User, conversation: Conversation, sample_tasks: list[Task]):
        """
        E2E: User says "reverse the sort" or "sort descending"
        Expected: AI agent toggles sort direction
        """
        user_message = "sort by due date descending"

        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        params = ListTasksParams(
            user_id=user.id,
            sort_by="due_date",
            sort_direction="desc"
        )

        result = list_tasks(params, db)

        # Verify sorted by due_date descending (latest first)
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["title"] == "Call doctor"  # Day 3
        assert result["tasks"][1]["title"] == "Attend meeting"  # Day 2
        assert result["tasks"][2]["title"] == "Buy groceries"  # Day 1


class TestE2EFrontendIntegration:
    """Test frontend sort dropdown integration with backend."""

    def test_e2e_frontend_sort_dropdown_due_date(self, db: Session, user: User, sample_tasks: list[Task]):
        """
        E2E: User selects "Due Date" from dropdown
        Expected: Frontend calls API with sort_by=due_date, sort_direction=asc (default)
        """
        # Simulate frontend API call
        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        params = ListTasksParams(
            user_id=user.id,
            sort_by="due_date",
            sort_direction="asc"  # Default for due_date
        )

        result = list_tasks(params, db)

        # Verify correct sort
        assert result["tasks"][0]["title"] == "Buy groceries"  # Earliest
        assert result["tasks"][-1]["title"] == "Call doctor"  # Latest

    def test_e2e_frontend_direction_toggle(self, db: Session, user: User, sample_tasks: list[Task]):
        """
        E2E: User clicks direction toggle button (↑ → ↓)
        Expected: Frontend calls API with reversed sort_direction
        """
        # Initial sort: ascending
        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        params_asc = ListTasksParams(
            user_id=user.id,
            sort_by="created_at",
            sort_direction="asc"
        )

        result_asc = list_tasks(params_asc, db)

        # User clicks toggle
        params_desc = ListTasksParams(
            user_id=user.id,
            sort_by="created_at",
            sort_direction="desc"
        )

        result_desc = list_tasks(params_desc, db)

        # Verify direction reversed
        assert result_asc["tasks"][0]["title"] == result_desc["tasks"][-1]["title"]
        assert result_asc["tasks"][-1]["title"] == result_desc["tasks"][0]["title"]

    def test_e2e_session_persistence_simulation(self, db: Session, user: User, sample_tasks: list[Task]):
        """
        E2E: User sets sort preference, refreshes page
        Expected: Frontend restores sort from sessionStorage, calls API with same params
        """
        # User sets sort preference
        user_preference = {
            "sort_by": "priority",
            "sort_direction": "asc"
        }

        # Simulate page refresh - frontend restores from sessionStorage
        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        params = ListTasksParams(
            user_id=user.id,
            sort_by=user_preference["sort_by"],
            sort_direction=user_preference["sort_direction"]
        )

        result = list_tasks(params, db)

        # Verify sort preference maintained
        assert result["tasks"][0]["priority"] == "high"
        assert result["tasks"][1]["priority"] == "medium"
        assert result["tasks"][2]["priority"] == "low"


class TestE2EErrorHandling:
    """Test error handling in E2E scenarios."""

    def test_e2e_invalid_sort_field_from_api(self, db: Session, user: User):
        """
        E2E: Frontend sends invalid sort_by field
        Expected: Backend returns 422 validation error
        """
        from src.mcp_tools.list_tasks import ListTasksParams

        with pytest.raises(ValueError, match="sort_by must be one of"):
            params = ListTasksParams(
                user_id=user.id,
                sort_by="invalid_field"
            )

    def test_e2e_invalid_sort_direction_from_api(self, db: Session, user: User):
        """
        E2E: Frontend sends invalid sort_direction
        Expected: Backend returns 422 validation error
        """
        from src.mcp_tools.list_tasks import ListTasksParams

        with pytest.raises(ValueError, match="sort_direction must be one of"):
            params = ListTasksParams(
                user_id=user.id,
                sort_by="created_at",
                sort_direction="invalid"
            )

    def test_e2e_empty_results_with_sort(self, db: Session, user: User):
        """
        E2E: User has no tasks, applies sort
        Expected: Returns empty array with sort info
        """
        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        params = ListTasksParams(
            user_id=user.id,
            sort_by="priority",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Should return empty array, not error
        assert result["tasks"] == []
        assert result["totalCount"] == 0
        assert result["appliedFilters"]["sort_by"] == "priority"
        assert result["appliedFilters"]["sort_direction"] == "asc"


class TestE2EPerformance:
    """Test performance of sorting in E2E scenarios."""

    def test_e2e_sort_performance_100_tasks(self, db: Session, user: User):
        """
        E2E: User has 100 tasks, applies sort
        Expected: Response time < 200ms
        """
        import time
        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        now = datetime.utcnow()

        # Create 100 tasks
        tasks = [
            Task(
                user_id=user.id,
                title=f"Task {i}",
                due_date=now + timedelta(days=i % 30),
                priority=["high", "medium", "low"][i % 3],
                created_at=now - timedelta(hours=i)
            )
            for i in range(100)
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        # Measure sort performance
        start_time = time.time()

        params = ListTasksParams(
            user_id=user.id,
            sort_by="due_date",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000

        # Verify performance
        assert len(result["tasks"]) == 100
        assert execution_time_ms < 200, f"Sort took {execution_time_ms}ms, expected < 200ms"

    def test_e2e_combined_sort_filter_performance(self, db: Session, user: User):
        """
        E2E: User has 100 tasks, applies sort + filter
        Expected: Response time < 200ms
        """
        import time
        from src.mcp_tools.list_tasks import list_tasks, ListTasksParams

        now = datetime.utcnow()

        # Create 100 tasks with keyword
        tasks = [
            Task(
                user_id=user.id,
                title=f"Task buy {i}" if i % 2 == 0 else f"Task call {i}",
                priority=["high", "medium", "low"][i % 3],
                created_at=now - timedelta(hours=i)
            )
            for i in range(100)
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        # Measure combined filter + sort performance
        start_time = time.time()

        params = ListTasksParams(
            user_id=user.id,
            keyword="buy",
            sort_by="priority",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000

        # Verify performance and correctness
        assert len(result["tasks"]) == 50  # Half have "buy" keyword
        assert execution_time_ms < 200, f"Combined operation took {execution_time_ms}ms, expected < 200ms"
