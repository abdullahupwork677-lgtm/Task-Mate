"""
Shared pytest fixtures for all tests.

Provides database session and test user fixtures for integration tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
import os

# Skip database tests when no DB is available
SKIP_DB_TESTS = os.environ.get('SKIP_DB_TESTS', 'true').lower() == 'true'


@pytest.fixture
def mock_db():
    """Create a mock database session for unit/edge tests."""
    db = Mock()
    db.exec = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def test_user_id():
    """Return a test user ID."""
    return "test-user-123"


# Real database fixtures (for integration tests with actual DB)
@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for testing."""
    if SKIP_DB_TESTS:
        pytest.skip("Database tests skipped (SKIP_DB_TESTS=true)")

    from sqlmodel import create_engine

    # Use test database URL if available
    test_db_url = os.environ.get('TEST_DATABASE_URL', 'postgresql://test:test@localhost:5432/test')
    engine = create_engine(test_db_url)
    return engine


@pytest.fixture
def db(db_engine, mock_db):
    """
    Create database session for tests.
    Uses mock_db when real DB is not available.
    """
    if SKIP_DB_TESTS:
        # Return mock DB for tests that don't need real DB
        return mock_db

    from sqlmodel import Session

    with Session(db_engine) as session:
        yield session
        session.rollback()  # Rollback after each test


# Mock fixtures for integration tests that don't need real DB
@pytest.fixture
def mock_task():
    """Create a mock task object."""
    task = Mock()
    task.id = 1
    task.task_id = 1
    task.user_id = "test-user-123"
    task.title = "Test Task"
    task.description = "Test description"
    task.priority = "medium"
    task.due_date = None
    task.completed = False
    task.created_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    return task


@pytest.fixture
def mock_conversation():
    """Create a mock conversation object."""
    conversation = Mock()
    conversation.id = 1
    conversation.user_id = "test-user-123"
    conversation.current_intent = "NEUTRAL"
    conversation.state_data = None
    conversation.target_task_id = None
    conversation.created_at = datetime.utcnow()
    conversation.updated_at = datetime.utcnow()
    return conversation


@pytest.fixture
def mock_conversation_service():
    """Create a mock conversation service."""
    service = Mock()
    service.update_conversation_state = Mock()
    service.reset_conversation_state = Mock()
    service.get_conversation_state = Mock(return_value={
        "current_intent": "NEUTRAL",
        "state_data": None,
        "target_task_id": None
    })
    return service


# Alias fixtures for consistency across test files
@pytest.fixture
def db_session(db):
    """Alias for db fixture - provides database session."""
    return db


@pytest.fixture
def test_user(db_session):
    """Create a test user in database for integration tests."""
    if SKIP_DB_TESTS:
        # Return mock user when DB is skipped
        user = Mock()
        user.id = "test-user-123"
        user.email = "test@example.com"
        user.name = "Test User"
        return user

    from src.models import User

    user = User(
        id="test-user-phase8",
        email="test.phase8@example.com",
        name="Test User Phase 8",
        hashed_password="$2b$12$dummy.hash.for.testing"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    # Cleanup after test
    db_session.delete(user)
    db_session.commit()
