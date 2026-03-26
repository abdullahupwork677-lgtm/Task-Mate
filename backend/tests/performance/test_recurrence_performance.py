"""Performance and Load Tests for Recurring Tasks

This module contains performance benchmarks and load tests to ensure
the recurring tasks feature meets performance SLAs:

- calculate_next_due_date(): < 10ms
- complete_task() with recurrence: < 200ms
- List 1000 recurring tasks: < 50ms (with indexes)
- Concurrent completions: 100 tasks in < 10s

Phase V: Performance & Load Testing (Phase 12)
"""

import time
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

import pytest
from sqlmodel import Session, select

from src.models import Task, User
from src.services.recurrence_engine import calculate_next_due_date
from src.mcp_tools.complete_task import complete_task, CompleteTaskParams


# Performance test markers
pytestmark = pytest.mark.performance


class TestRecurrenceEnginePerformance:
    """Performance tests for recurrence engine date calculations."""

    def test_calculate_next_due_date_performance_daily(self):
        """Test calculate_next_due_date completes in < 10ms for daily pattern.

        SLA: < 10ms per calculation
        Test: 1000 iterations, measure p50, p95, p99
        """
        current_date = datetime(2026, 2, 9, 9, 0, 0)
        pattern = "daily"
        iterations = 1000

        # Warmup (JIT compilation, cache warming)
        for _ in range(100):
            calculate_next_due_date(current_date, pattern)

        # Actual benchmark
        execution_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            result = calculate_next_due_date(current_date, pattern)
            end = time.perf_counter()
            execution_times.append((end - start) * 1000)  # Convert to ms

            # Verify correctness
            assert result == datetime(2026, 2, 10, 9, 0, 0)

        # Calculate statistics
        p50 = statistics.median(execution_times)
        p95 = statistics.quantiles(execution_times, n=100)[94]
        p99 = statistics.quantiles(execution_times, n=100)[98]
        mean = statistics.mean(execution_times)

        # Report
        print(f"\n{'='*60}")
        print(f"calculate_next_due_date() Performance (daily)")
        print(f"{'='*60}")
        print(f"Iterations: {iterations}")
        print(f"Mean:       {mean:.4f} ms")
        print(f"p50:        {p50:.4f} ms")
        print(f"p95:        {p95:.4f} ms")
        print(f"p99:        {p99:.4f} ms")
        print(f"{'='*60}")

        # Assert SLA: p95 < 10ms
        assert p95 < 10.0, f"p95 ({p95:.4f}ms) exceeds SLA (10ms)"

    def test_calculate_next_due_date_performance_monthly(self):
        """Test calculate_next_due_date completes in < 10ms for monthly pattern.

        Monthly calculations use relativedelta which is more complex.
        """
        current_date = datetime(2026, 1, 31, 9, 0, 0)  # Month-end edge case
        pattern = "monthly"
        iterations = 1000

        # Warmup
        for _ in range(100):
            calculate_next_due_date(current_date, pattern)

        # Benchmark
        execution_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            result = calculate_next_due_date(current_date, pattern)
            end = time.perf_counter()
            execution_times.append((end - start) * 1000)

            # Verify month-end handling (Jan 31 → Feb 28/29)
            assert result.month == 2
            assert result.day in [28, 29]  # Feb 28 or 29

        # Statistics
        p50 = statistics.median(execution_times)
        p95 = statistics.quantiles(execution_times, n=100)[94]
        mean = statistics.mean(execution_times)

        print(f"\n{'='*60}")
        print(f"calculate_next_due_date() Performance (monthly)")
        print(f"{'='*60}")
        print(f"Iterations: {iterations}")
        print(f"Mean:       {mean:.4f} ms")
        print(f"p50:        {p50:.4f} ms")
        print(f"p95:        {p95:.4f} ms")
        print(f"{'='*60}")

        # Assert SLA
        assert p95 < 10.0, f"p95 ({p95:.4f}ms) exceeds SLA (10ms)"

    def test_calculate_next_due_date_performance_custom(self):
        """Test calculate_next_due_date with custom patterns (every N days)."""
        current_date = datetime(2026, 2, 9, 9, 0, 0)
        pattern = "every 3 days"
        iterations = 1000

        # Warmup
        for _ in range(100):
            calculate_next_due_date(current_date, pattern)

        # Benchmark
        execution_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            result = calculate_next_due_date(current_date, pattern)
            end = time.perf_counter()
            execution_times.append((end - start) * 1000)

            assert result == datetime(2026, 2, 12, 9, 0, 0)

        # Statistics
        p95 = statistics.quantiles(execution_times, n=100)[94]

        print(f"\n{'='*60}")
        print(f"calculate_next_due_date() Performance (every 3 days)")
        print(f"{'='*60}")
        print(f"p95: {p95:.4f} ms")
        print(f"{'='*60}")

        assert p95 < 10.0, f"p95 ({p95:.4f}ms) exceeds SLA (10ms)"


class TestCompleteTaskPerformance:
    """Performance tests for completing recurring tasks."""

    def test_complete_recurring_task_performance(
        self, db_session: Session, test_user: User
    ):
        """Test complete_task() with auto-create completes in < 200ms.

        SLA: p95 < 200ms (includes DB write + next occurrence creation)
        """
        iterations = 100
        execution_times = []

        for i in range(iterations):
            # Create recurring task
            task = Task(
                user_id=test_user.id,
                title=f"Performance test task {i}",
                is_recurring=True,
                recurrence_pattern="daily",
                due_date=datetime(2026, 2, 9, 9, 0, 0),
                completed=False,
            )
            db_session.add(task)
            db_session.commit()
            db_session.refresh(task)

            # Benchmark completion (includes auto-create)
            params = CompleteTaskParams(user_id=test_user.id, task_id=task.id)

            start = time.perf_counter()
            result = complete_task(db_session, params)
            end = time.perf_counter()

            execution_times.append((end - start) * 1000)

            # Verify next occurrence created
            assert result.next_occurrence is not None
            assert result.next_occurrence.task_id > task.id

        # Statistics
        mean = statistics.mean(execution_times)
        p50 = statistics.median(execution_times)
        p95 = statistics.quantiles(execution_times, n=100)[94]
        p99 = statistics.quantiles(execution_times, n=100)[98]

        print(f"\n{'='*60}")
        print(f"complete_task() Performance (with auto-create)")
        print(f"{'='*60}")
        print(f"Iterations: {iterations}")
        print(f"Mean:       {mean:.4f} ms")
        print(f"p50:        {p50:.4f} ms")
        print(f"p95:        {p95:.4f} ms")
        print(f"p99:        {p99:.4f} ms")
        print(f"{'='*60}")

        # Assert SLA: p95 < 200ms
        assert p95 < 200.0, f"p95 ({p95:.4f}ms) exceeds SLA (200ms)"


class TestConcurrentCompletions:
    """Load tests for concurrent task completions."""

    def test_concurrent_completions_100_tasks(
        self, db_session: Session, test_user: User
    ):
        """Test completing 100 recurring tasks concurrently.

        Goal: Verify no duplicate next occurrences (idempotency)
        SLA: Complete all 100 in < 10s
        """
        num_tasks = 100

        # Create 100 recurring tasks
        task_ids = []
        for i in range(num_tasks):
            task = Task(
                user_id=test_user.id,
                title=f"Concurrent test task {i}",
                is_recurring=True,
                recurrence_pattern="daily",
                due_date=datetime(2026, 2, 9, 9, 0, 0),
                completed=False,
            )
            db_session.add(task)
        db_session.commit()

        # Get task IDs
        tasks = db_session.exec(
            select(Task).where(
                Task.user_id == test_user.id, Task.title.startswith("Concurrent test task")
            )
        ).all()
        task_ids = [task.id for task in tasks]

        def complete_single_task(task_id: int) -> Tuple[int, float, bool]:
            """Complete a single task and return timing + success."""
            # Create new session for thread safety
            with Session(db_session.get_bind()) as session:
                params = CompleteTaskParams(user_id=test_user.id, task_id=task_id)
                start = time.perf_counter()
                try:
                    result = complete_task(session, params)
                    end = time.perf_counter()
                    has_next = result.next_occurrence is not None
                    return (task_id, (end - start) * 1000, has_next)
                except Exception as e:
                    end = time.perf_counter()
                    print(f"Error completing task {task_id}: {e}")
                    return (task_id, (end - start) * 1000, False)

        # Execute concurrently
        start_total = time.perf_counter()
        results = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(complete_single_task, tid) for tid in task_ids]
            for future in as_completed(futures):
                results.append(future.result())

        end_total = time.perf_counter()
        total_time = (end_total - start_total) * 1000

        # Analyze results
        completion_times = [r[1] for r in results]
        next_created_count = sum(1 for r in results if r[2])

        mean = statistics.mean(completion_times)
        p95 = statistics.quantiles(completion_times, n=100)[94]

        print(f"\n{'='*60}")
        print(f"Concurrent Completions Load Test")
        print(f"{'='*60}")
        print(f"Tasks:              {num_tasks}")
        print(f"Workers:            10")
        print(f"Total time:         {total_time:.2f} ms ({total_time/1000:.2f}s)")
        print(f"Next created:       {next_created_count}/{num_tasks}")
        print(f"Mean per task:      {mean:.4f} ms")
        print(f"p95 per task:       {p95:.4f} ms")
        print(f"Throughput:         {(num_tasks / (total_time/1000)):.2f} tasks/sec")
        print(f"{'='*60}")

        # Assertions
        assert total_time < 10000, f"Total time ({total_time:.2f}ms) exceeds 10s"
        assert next_created_count == num_tasks, "Not all next occurrences created"

        # Verify no duplicates (idempotency check)
        all_tasks = db_session.exec(
            select(Task).where(Task.user_id == test_user.id)
        ).all()

        # Count parent_task_id occurrences
        parent_counts = {}
        for task in all_tasks:
            if task.parent_task_id:
                parent_counts[task.parent_task_id] = (
                    parent_counts.get(task.parent_task_id, 0) + 1
                )

        # Each parent should have exactly 1 child (next occurrence)
        duplicates = [
            (parent, count) for parent, count in parent_counts.items() if count > 1
        ]
        assert len(duplicates) == 0, f"Duplicate next occurrences found: {duplicates}"


class TestListRecurringTasksPerformance:
    """Performance tests for listing recurring tasks."""

    def test_list_1000_recurring_tasks_performance(
        self, db_session: Session, test_user: User
    ):
        """Test listing 1000 recurring tasks completes in < 50ms.

        SLA: < 50ms with composite index on (user_id, is_recurring)
        """
        num_tasks = 1000

        # Create 1000 recurring tasks
        print(f"\nCreating {num_tasks} recurring tasks...")
        for i in range(num_tasks):
            task = Task(
                user_id=test_user.id,
                title=f"Recurring task {i}",
                is_recurring=True,
                recurrence_pattern="daily",
                due_date=datetime(2026, 2, 9, 9, 0, 0) + timedelta(days=i % 30),
                completed=False,
            )
            db_session.add(task)

            # Batch commit every 100 tasks
            if (i + 1) % 100 == 0:
                db_session.commit()

        db_session.commit()
        print(f"Created {num_tasks} tasks")

        # Warmup query (to warm DB cache)
        for _ in range(10):
            _ = db_session.exec(
                select(Task).where(
                    Task.user_id == test_user.id, Task.is_recurring == True
                )
            ).all()

        # Benchmark query
        iterations = 100
        execution_times = []

        for _ in range(iterations):
            start = time.perf_counter()
            recurring_tasks = db_session.exec(
                select(Task).where(
                    Task.user_id == test_user.id, Task.is_recurring == True
                )
            ).all()
            end = time.perf_counter()

            execution_times.append((end - start) * 1000)
            assert len(recurring_tasks) >= num_tasks

        # Statistics
        mean = statistics.mean(execution_times)
        p50 = statistics.median(execution_times)
        p95 = statistics.quantiles(execution_times, n=100)[94]
        p99 = statistics.quantiles(execution_times, n=100)[98]

        print(f"\n{'='*60}")
        print(f"List Recurring Tasks Performance")
        print(f"{'='*60}")
        print(f"Tasks:      {num_tasks}")
        print(f"Iterations: {iterations}")
        print(f"Mean:       {mean:.4f} ms")
        print(f"p50:        {p50:.4f} ms")
        print(f"p95:        {p95:.4f} ms")
        print(f"p99:        {p99:.4f} ms")
        print(f"{'='*60}")

        # Assert SLA: p95 < 50ms (with index)
        assert (
            p95 < 50.0
        ), f"p95 ({p95:.4f}ms) exceeds SLA (50ms). Index may be missing!"


class TestIndexUsage:
    """Tests to verify database indexes are being used."""

    def test_composite_index_usage(self, db_session: Session, test_user: User):
        """Verify ix_tasks_user_recurring index is used for recurring task queries.

        Uses EXPLAIN to check query plan.
        """
        # Create sample data
        for i in range(10):
            task = Task(
                user_id=test_user.id,
                title=f"Test task {i}",
                is_recurring=i % 2 == 0,
                recurrence_pattern="daily" if i % 2 == 0 else None,
                completed=False,
            )
            db_session.add(task)
        db_session.commit()

        # Get query plan
        query = (
            "EXPLAIN SELECT * FROM tasks "
            "WHERE user_id = :user_id AND is_recurring = TRUE"
        )
        result = db_session.execute(query, {"user_id": test_user.id})
        plan = "\n".join([row[0] for row in result])

        print(f"\n{'='*60}")
        print(f"Query Plan for Recurring Tasks Query")
        print(f"{'='*60}")
        print(plan)
        print(f"{'='*60}")

        # Verify index is used (PostgreSQL specific)
        # Look for "Index Scan" or index name in plan
        assert (
            "ix_tasks_user_recurring" in plan or "Index Scan" in plan
        ), "Composite index not being used!"

    def test_unique_index_usage(self, db_session: Session, test_user: User):
        """Verify ix_tasks_parent_due_unique index is used for duplicate prevention.

        This index enforces idempotency for next occurrence creation.
        """
        # Create parent task
        parent = Task(
            user_id=test_user.id,
            title="Parent task",
            is_recurring=True,
            recurrence_pattern="daily",
            completed=True,
        )
        db_session.add(parent)
        db_session.commit()

        # Create next occurrence
        next_task = Task(
            user_id=test_user.id,
            title="Next occurrence",
            parent_task_id=parent.id,
            due_date=datetime(2026, 2, 10, 9, 0, 0),
            is_recurring=True,
            recurrence_pattern="daily",
            completed=False,
        )
        db_session.add(next_task)
        db_session.commit()

        # Try to create duplicate (should fail via unique constraint)
        duplicate = Task(
            user_id=test_user.id,
            title="Duplicate next occurrence",
            parent_task_id=parent.id,
            due_date=datetime(2026, 2, 10, 9, 0, 0),  # Same date!
            is_recurring=True,
            recurrence_pattern="daily",
            completed=False,
        )
        db_session.add(duplicate)

        # Should raise IntegrityError
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

        print(f"\n{'='*60}")
        print(f"Unique Index Validation")
        print(f"{'='*60}")
        print(f"✅ Unique constraint enforced (duplicate prevented)")
        print(f"Index: ix_tasks_parent_due_unique")
        print(f"Columns: (parent_task_id, due_date)")
        print(f"{'='*60}")


# Performance test configuration
@pytest.fixture(scope="module")
def db_session():
    """Database session for performance tests.

    Note: Uses same db fixture as other tests.
    """
    from tests.conftest import db

    return db()


@pytest.fixture(scope="module")
def test_user(db_session):
    """Create test user for performance tests."""
    user = User(
        id="perf-test-user",
        email="perf@test.com",
        hashed_password="hashed",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
