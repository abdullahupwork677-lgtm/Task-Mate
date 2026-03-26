"""
Unit Tests: Task Sorting (Feature 005-task-sort)

Tests all sort fields (due_date, priority, created_at, title) with both
ascending and descending directions. Validates NULL handling, case-insensitive
sorting, priority mapping, and tiebreaker logic.

Phase: 005-task-sort (Phase V)
Task: T033 (Unit testing)
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session, select
from src.models import Task, User
from src.services.task_service import TaskService


@pytest.fixture
def user(db: Session) -> User:
    """Create test user."""
    user = User(
        id="test-user-id",
        email="test@example.com",
        hashed_password="hashed"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def task_service(db: Session) -> TaskService:
    """Create TaskService instance."""
    return TaskService(db)


@pytest.fixture
def sample_tasks(db: Session, user: User) -> list[Task]:
    """Create sample tasks with various attributes for sorting tests."""
    now = datetime.utcnow()

    tasks = [
        # Tasks with due dates
        Task(
            user_id=user.id,
            title="Zebra task",
            due_date=now + timedelta(days=1),
            priority="high",
            created_at=now - timedelta(hours=10)
        ),
        Task(
            user_id=user.id,
            title="Apple task",
            due_date=now + timedelta(days=3),
            priority="medium",
            created_at=now - timedelta(hours=8)
        ),
        Task(
            user_id=user.id,
            title="Banana task",
            due_date=now + timedelta(days=2),
            priority="low",
            created_at=now - timedelta(hours=6)
        ),

        # Tasks without due dates (should appear at end when sorting by due_date)
        Task(
            user_id=user.id,
            title="Charlie task",
            due_date=None,
            priority="high",
            created_at=now - timedelta(hours=4)
        ),
        Task(
            user_id=user.id,
            title="Delta task",
            due_date=None,
            priority="medium",
            created_at=now - timedelta(hours=2)
        ),

        # Task for case-insensitive title sorting
        Task(
            user_id=user.id,
            title="UPPERCASE task",
            due_date=now + timedelta(days=4),
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


class TestSortByDueDate:
    """Test suite for sorting by due_date."""

    def test_sort_by_due_date_asc(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test sorting by due date ascending (earliest first)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="due_date",
            sort_direction="asc"
        )

        tasks = result["tasks"]

        # Should return tasks with due dates first (earliest → latest)
        # Then tasks without due dates (sorted by created_at DESC as tiebreaker)
        assert len(tasks) == 6

        # First 4 tasks should have due dates in ascending order
        assert tasks[0].title == "Zebra task"  # Day 1
        assert tasks[1].title == "Banana task"  # Day 2
        assert tasks[2].title == "Apple task"  # Day 3
        assert tasks[3].title == "UPPERCASE task"  # Day 4

        # Last 2 tasks should have NULL due_date (newest first by created_at)
        assert tasks[4].due_date is None
        assert tasks[5].due_date is None
        assert tasks[4].title == "Delta task"  # More recent created_at
        assert tasks[5].title == "Charlie task"  # Older created_at

    def test_sort_by_due_date_desc(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test sorting by due date descending (latest first)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="due_date",
            sort_direction="desc"
        )

        tasks = result["tasks"]

        # Should return tasks with due dates first (latest → earliest)
        # Then tasks without due dates at end
        assert len(tasks) == 6

        # First 4 tasks in descending due date order
        assert tasks[0].title == "UPPERCASE task"  # Day 4
        assert tasks[1].title == "Apple task"  # Day 3
        assert tasks[2].title == "Banana task"  # Day 2
        assert tasks[3].title == "Zebra task"  # Day 1

        # Last 2 tasks have NULL due_date
        assert tasks[4].due_date is None
        assert tasks[5].due_date is None

    def test_null_due_dates_always_at_end(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test that NULL due dates always appear at end regardless of direction."""
        # Ascending
        result_asc = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="due_date",
            sort_direction="asc"
        )

        tasks_asc = result_asc["tasks"]
        assert tasks_asc[-1].due_date is None  # Last task has NULL
        assert tasks_asc[-2].due_date is None  # Second-to-last has NULL

        # Descending
        result_desc = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="due_date",
            sort_direction="desc"
        )

        tasks_desc = result_desc["tasks"]
        assert tasks_desc[-1].due_date is None
        assert tasks_desc[-2].due_date is None


class TestSortByPriority:
    """Test suite for sorting by priority."""

    def test_sort_by_priority_asc_high_to_low(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test sorting by priority ascending (high → medium → low)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="priority",
            sort_direction="asc"
        )

        tasks = result["tasks"]

        # Extract priorities
        priorities = [task.priority for task in tasks]

        # Should group by priority: high, then medium, then low
        # Within each group, sorted by created_at DESC (newest first)

        # Count each priority
        high_count = priorities.count("high")
        medium_count = priorities.count("medium")
        low_count = priorities.count("low")

        assert high_count == 2
        assert medium_count == 2
        assert low_count == 2

        # First 2 should be high priority
        assert tasks[0].priority == "high"
        assert tasks[1].priority == "high"

        # Next 2 should be medium
        assert tasks[2].priority == "medium"
        assert tasks[3].priority == "medium"

        # Last 2 should be low
        assert tasks[4].priority == "low"
        assert tasks[5].priority == "low"

        # Within high priority group, check created_at DESC tiebreaker
        if tasks[0].priority == "high" and tasks[1].priority == "high":
            assert tasks[0].created_at >= tasks[1].created_at

    def test_sort_by_priority_desc_low_to_high(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test sorting by priority descending (low → medium → high)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="priority",
            sort_direction="desc"
        )

        tasks = result["tasks"]
        priorities = [task.priority for task in tasks]

        # Should be reversed: low, then medium, then high

        # First 2 should be low priority
        assert tasks[0].priority == "low"
        assert tasks[1].priority == "low"

        # Next 2 should be medium
        assert tasks[2].priority == "medium"
        assert tasks[3].priority == "medium"

        # Last 2 should be high
        assert tasks[4].priority == "high"
        assert tasks[5].priority == "high"


class TestSortByCreatedAt:
    """Test suite for sorting by created_at."""

    def test_sort_by_created_at_asc_oldest_first(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test sorting by created_at ascending (oldest first)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="created_at",
            sort_direction="asc"
        )

        tasks = result["tasks"]

        # Should be in ascending order (oldest → newest)
        assert len(tasks) == 6

        # Verify chronological order
        for i in range(len(tasks) - 1):
            assert tasks[i].created_at <= tasks[i + 1].created_at

        # Oldest task first
        assert tasks[0].title == "Zebra task"  # Created 10 hours ago

        # Newest task last
        assert tasks[-1].title == "UPPERCASE task"  # Created 1 hour ago

    def test_sort_by_created_at_desc_newest_first(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test sorting by created_at descending (newest first) - DEFAULT."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="created_at",
            sort_direction="desc"
        )

        tasks = result["tasks"]

        # Should be in descending order (newest → oldest)
        assert len(tasks) == 6

        # Verify reverse chronological order
        for i in range(len(tasks) - 1):
            assert tasks[i].created_at >= tasks[i + 1].created_at

        # Newest task first
        assert tasks[0].title == "UPPERCASE task"  # Created 1 hour ago

        # Oldest task last
        assert tasks[-1].title == "Zebra task"  # Created 10 hours ago

    def test_default_sort_is_created_at_desc(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test that default sort is created_at DESC (newest first)."""
        # No sort parameters - should use default
        result = task_service.search_and_filter_tasks(
            user_id=user.id
        )

        tasks = result["tasks"]

        # Should be sorted by created_at DESC (default)
        assert tasks[0].title == "UPPERCASE task"  # Newest
        assert tasks[-1].title == "Zebra task"  # Oldest


class TestSortByTitle:
    """Test suite for sorting by title (alphabetically)."""

    def test_sort_by_title_asc_a_to_z(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test sorting by title ascending (A → Z, case-insensitive)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="title",
            sort_direction="asc"
        )

        tasks = result["tasks"]

        # Should be alphabetical (case-insensitive)
        titles = [task.title for task in tasks]

        assert titles[0] == "Apple task"  # A
        assert titles[1] == "Banana task"  # B
        assert titles[2] == "Charlie task"  # C
        assert titles[3] == "Delta task"  # D
        assert titles[4] == "UPPERCASE task"  # U (case-insensitive)
        assert titles[5] == "Zebra task"  # Z

    def test_sort_by_title_desc_z_to_a(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test sorting by title descending (Z → A)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="title",
            sort_direction="desc"
        )

        tasks = result["tasks"]
        titles = [task.title for task in tasks]

        # Should be reverse alphabetical
        assert titles[0] == "Zebra task"  # Z
        assert titles[1] == "UPPERCASE task"  # U
        assert titles[2] == "Delta task"  # D
        assert titles[3] == "Charlie task"  # C
        assert titles[4] == "Banana task"  # B
        assert titles[5] == "Apple task"  # A

    def test_title_sort_case_insensitive(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test that title sorting is case-insensitive."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="title",
            sort_direction="asc"
        )

        tasks = result["tasks"]

        # "UPPERCASE task" should be sorted as "uppercase task"
        # So it should appear between T and Z
        uppercase_task = next(t for t in tasks if t.title == "UPPERCASE task")
        uppercase_index = tasks.index(uppercase_task)

        # Should be sorted alphabetically by lowercase version
        assert uppercase_index == 4  # Between D and Z


class TestSortDefaultDirections:
    """Test suite for field-specific default sort directions."""

    def test_default_direction_due_date_is_asc(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test that due_date defaults to asc (earliest first)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="due_date",
            sort_direction=None  # Use default
        )

        tasks = result["tasks"]

        # Default should be asc (earliest first)
        # First task should have earliest due date
        assert tasks[0].title == "Zebra task"  # Day 1 (earliest)

    def test_default_direction_priority_is_asc(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test that priority defaults to asc (high → low)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="priority",
            sort_direction=None  # Use default
        )

        tasks = result["tasks"]

        # Default should be asc (high first)
        assert tasks[0].priority == "high"
        assert tasks[1].priority == "high"

    def test_default_direction_created_at_is_desc(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test that created_at defaults to desc (newest first)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="created_at",
            sort_direction=None  # Use default
        )

        tasks = result["tasks"]

        # Default should be desc (newest first)
        assert tasks[0].title == "UPPERCASE task"  # Newest

    def test_default_direction_title_is_asc(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test that title defaults to asc (A → Z)."""
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="title",
            sort_direction=None  # Use default
        )

        tasks = result["tasks"]

        # Default should be asc (A → Z)
        assert tasks[0].title == "Apple task"  # A


class TestSortValidation:
    """Test suite for sort parameter validation."""

    def test_invalid_sort_field_raises_error(self, task_service: TaskService, user: User):
        """Test that invalid sort field raises validation error."""
        with pytest.raises(ValueError, match="Invalid sort_by"):
            task_service.search_and_filter_tasks(
                user_id=user.id,
                sort_by="invalid_field"
            )

    def test_invalid_sort_direction_raises_error(self, task_service: TaskService, user: User):
        """Test that invalid sort direction raises validation error."""
        with pytest.raises(ValueError, match="Invalid sort_direction"):
            task_service.search_and_filter_tasks(
                user_id=user.id,
                sort_by="created_at",
                sort_direction="invalid"
            )

    def test_valid_sort_fields(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test that all valid sort fields work."""
        valid_fields = ["due_date", "priority", "created_at", "title"]

        for field in valid_fields:
            result = task_service.search_and_filter_tasks(
                user_id=user.id,
                sort_by=field,
                sort_direction="asc"
            )

            assert "tasks" in result
            assert len(result["tasks"]) > 0

    def test_valid_sort_directions(self, task_service: TaskService, user: User, sample_tasks: list[Task]):
        """Test that both asc and desc directions work."""
        for direction in ["asc", "desc"]:
            result = task_service.search_and_filter_tasks(
                user_id=user.id,
                sort_by="created_at",
                sort_direction=direction
            )

            assert "tasks" in result
            assert len(result["tasks"]) > 0


class TestSortCombinedWithFilters:
    """Test suite for sorting combined with search/filter."""

    def test_sort_with_status_filter(self, task_service: TaskService, user: User, db: Session):
        """Test sorting works with status filter."""
        # Create tasks with different statuses
        now = datetime.utcnow()
        tasks = [
            Task(user_id=user.id, title="Task A", completed=True, created_at=now - timedelta(hours=3)),
            Task(user_id=user.id, title="Task B", completed=False, created_at=now - timedelta(hours=2)),
            Task(user_id=user.id, title="Task C", completed=True, created_at=now - timedelta(hours=1)),
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        # Filter completed + sort by created_at desc
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            status_filter="completed",
            sort_by="created_at",
            sort_direction="desc"
        )

        tasks = result["tasks"]

        # Should return only completed tasks, sorted newest first
        assert len(tasks) == 2
        assert all(t.completed for t in tasks)
        assert tasks[0].title == "Task C"  # Newest completed
        assert tasks[1].title == "Task A"  # Older completed

    def test_sort_with_keyword_search(self, task_service: TaskService, user: User, db: Session):
        """Test sorting works with keyword search."""
        # Create tasks with keyword
        now = datetime.utcnow()
        tasks = [
            Task(user_id=user.id, title="Buy groceries", priority="high", created_at=now - timedelta(hours=3)),
            Task(user_id=user.id, title="Buy milk", priority="low", created_at=now - timedelta(hours=2)),
            Task(user_id=user.id, title="Buy bread", priority="medium", created_at=now - timedelta(hours=1)),
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        # Search "buy" + sort by priority
        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            keyword="buy",
            sort_by="priority",
            sort_direction="asc"
        )

        tasks = result["tasks"]

        # Should return all 3 "buy" tasks sorted by priority
        assert len(tasks) == 3
        assert tasks[0].priority == "high"  # High first
        assert tasks[1].priority == "medium"
        assert tasks[2].priority == "low"


class TestSortTiebreakerLogic:
    """Test suite for tiebreaker logic (created_at DESC)."""

    def test_tiebreaker_for_same_due_date(self, task_service: TaskService, user: User, db: Session):
        """Test that tasks with same due date are sorted by created_at DESC."""
        now = datetime.utcnow()
        due_date = now + timedelta(days=1)

        tasks = [
            Task(user_id=user.id, title="Task A", due_date=due_date, created_at=now - timedelta(hours=3)),
            Task(user_id=user.id, title="Task B", due_date=due_date, created_at=now - timedelta(hours=1)),
            Task(user_id=user.id, title="Task C", due_date=due_date, created_at=now - timedelta(hours=2)),
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="due_date",
            sort_direction="asc"
        )

        returned_tasks = result["tasks"]

        # All have same due date, so should be sorted by created_at DESC (newest first)
        assert returned_tasks[0].title == "Task B"  # Newest (1 hour ago)
        assert returned_tasks[1].title == "Task C"  # Middle (2 hours ago)
        assert returned_tasks[2].title == "Task A"  # Oldest (3 hours ago)

    def test_tiebreaker_for_same_priority(self, task_service: TaskService, user: User, db: Session):
        """Test that tasks with same priority are sorted by created_at DESC."""
        now = datetime.utcnow()

        tasks = [
            Task(user_id=user.id, title="Task A", priority="high", created_at=now - timedelta(hours=3)),
            Task(user_id=user.id, title="Task B", priority="high", created_at=now - timedelta(hours=1)),
            Task(user_id=user.id, title="Task C", priority="high", created_at=now - timedelta(hours=2)),
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        result = task_service.search_and_filter_tasks(
            user_id=user.id,
            sort_by="priority",
            sort_direction="asc"
        )

        returned_tasks = result["tasks"]

        # All have same priority, so should be sorted by created_at DESC
        assert returned_tasks[0].title == "Task B"  # Newest
        assert returned_tasks[1].title == "Task C"  # Middle
        assert returned_tasks[2].title == "Task A"  # Oldest
