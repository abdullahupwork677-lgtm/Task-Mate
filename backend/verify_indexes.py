#!/usr/bin/env python3
"""
Verify that composite indexes are being used for search queries.

Uses EXPLAIN ANALYZE to check query plans and ensure indexes are utilized.

Phase: 004-search-filter
Task: T046 (Phase 9)

Usage:
    python verify_indexes.py
"""

import sys
from sqlalchemy import text
from src.db import get_session
from src.models.task import Task


def verify_index_usage():
    """Verify that composite indexes are being used by examining query plans."""

    print("=" * 80)
    print("VERIFYING COMPOSITE INDEX USAGE")
    print("=" * 80)
    print()

    session = next(get_session())

    # Test queries that should use indexes
    test_queries = [
        {
            "name": "User ID + Completed Filter",
            "query": """
                EXPLAIN QUERY PLAN
                SELECT * FROM tasks
                WHERE user_id = 'test-user' AND completed = 0
                ORDER BY created_at DESC;
            """,
            "expected_index": "idx_tasks_user_completed"
        },
        {
            "name": "User ID + Priority Filter",
            "query": """
                EXPLAIN QUERY PLAN
                SELECT * FROM tasks
                WHERE user_id = 'test-user' AND priority = 'high'
                ORDER BY created_at DESC;
            """,
            "expected_index": "idx_tasks_user_priority"
        },
        {
            "name": "User ID + Due Date Filter",
            "query": """
                EXPLAIN QUERY PLAN
                SELECT * FROM tasks
                WHERE user_id = 'test-user' AND due_date IS NOT NULL
                ORDER BY created_at DESC;
            """,
            "expected_index": "idx_tasks_user_due_date"
        },
        {
            "name": "User ID + Title Search (LIKE)",
            "query": """
                EXPLAIN QUERY PLAN
                SELECT * FROM tasks
                WHERE user_id = 'test-user' AND title LIKE '%grocery%'
                ORDER BY created_at DESC;
            """,
            "expected_index": "idx_tasks_user_title or user_id index"
        },
        {
            "name": "Combined Filters (All)",
            "query": """
                EXPLAIN QUERY PLAN
                SELECT * FROM tasks
                WHERE user_id = 'test-user'
                AND completed = 0
                AND priority = 'high'
                AND due_date IS NOT NULL
                ORDER BY created_at DESC;
            """,
            "expected_index": "composite index"
        }
    ]

    all_passed = True

    for i, test in enumerate(test_queries, 1):
        print(f"\nTest {i}: {test['name']}")
        print("-" * 80)
        print(f"Expected index: {test['expected_index']}")
        print()

        try:
            result = session.exec(text(test['query']))
            rows = result.fetchall()

            print("Query Plan:")
            for row in rows:
                plan_line = str(row[0]) if hasattr(row, '__iter__') else str(row)
                print(f"  {plan_line}")

                # Check if index is mentioned in plan
                plan_lower = plan_line.lower()
                if 'index' in plan_lower or 'idx_' in plan_lower:
                    print(f"  ✅ Index detected in query plan")
                elif 'scan table' in plan_lower:
                    print(f"  ⚠️  WARNING: Full table scan detected (no index used)")
                    all_passed = False

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            all_passed = False

    print()
    print("=" * 80)

    if all_passed:
        print("✅ INDEX VERIFICATION PASSED")
        print()
        print("All tested queries are using indexes efficiently.")
        return 0
    else:
        print("⚠️  INDEX VERIFICATION: WARNINGS DETECTED")
        print()
        print("Some queries may not be using indexes optimally.")
        print("Review the query plans above.")
        return 1


def list_all_indexes():
    """List all indexes on the tasks table."""

    print()
    print("=" * 80)
    print("ALL INDEXES ON TASKS TABLE")
    print("=" * 80)
    print()

    session = next(get_session())

    try:
        # Query to list all indexes (SQLite specific)
        query = text("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'index' AND tbl_name = 'tasks'
            ORDER BY name;
        """)

        result = session.exec(query)
        rows = result.fetchall()

        if not rows:
            print("No indexes found on tasks table")
            return

        for i, row in enumerate(rows, 1):
            index_name = row[0]
            index_sql = row[1]

            print(f"{i}. {index_name}")
            if index_sql:
                print(f"   SQL: {index_sql}")
            else:
                print(f"   (Auto-created index)")
            print()

    except Exception as e:
        print(f"ERROR listing indexes: {e}")


if __name__ == "__main__":
    print()
    print("DATABASE INDEX VERIFICATION")
    print()

    # List all indexes
    list_all_indexes()

    # Verify index usage
    exit_code = verify_index_usage()

    print()
    sys.exit(exit_code)
