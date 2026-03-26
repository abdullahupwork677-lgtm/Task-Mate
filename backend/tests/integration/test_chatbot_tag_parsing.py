"""Integration tests for chatbot natural language tag extraction.

Tests that the MCP tool correctly handles tags from natural language inputs
that the AI agent would extract. Since the actual NLP parsing is done by the
LLM (OpenAI GPT-4), these tests verify the MCP tool accepts and processes
tags correctly.

Examples of natural language inputs:
- "add task buy groceries, tags: shopping, urgent"
- "create task with tags work and important"
- "add buy milk with tag shopping"
"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.models import User, Task
from src.mcp_tools.add_task import add_task, AddTaskParams


@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """Create a test user."""
    user = User(
        id="test-user-123",
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    return user.id


class TestChatbotTagParsing:
    """Test tag extraction scenarios from natural language."""

    def test_explicit_tags_suffix(self, session: Session, test_user: str):
        """User says: 'add task buy groceries, tags: shopping, urgent'"""
        # LLM extracts: title="buy groceries", tags=["shopping", "urgent"]
        params = AddTaskParams(
            user_id=test_user,
            title="buy groceries",
            tags=["shopping", "urgent"]
        )

        result = add_task(session, params)

        assert result.title == "buy groceries"
        assert set(result.tags) == {"shopping", "urgent"}

    def test_tags_with_keyword(self, session: Session, test_user: str):
        """User says: 'create task call clients with tags work and important'"""
        # LLM extracts: title="call clients", tags=["work", "important"]
        params = AddTaskParams(
            user_id=test_user,
            title="call clients",
            tags=["work", "important"],
            priority="high"  # "important" might also influence priority
        )

        result = add_task(session, params)

        assert result.title == "call clients"
        assert "work" in result.tags
        assert "important" in result.tags

    def test_single_tag_mention(self, session: Session, test_user: str):
        """User says: 'add buy milk with tag shopping'"""
        # LLM extracts: title="buy milk", tags=["shopping"]
        params = AddTaskParams(
            user_id=test_user,
            title="buy milk",
            tags=["shopping"]
        )

        result = add_task(session, params)

        assert result.title == "buy milk"
        assert result.tags == ["shopping"]

    def test_multiple_tags_with_commas(self, session: Session, test_user: str):
        """User says: 'add task review code, tags: work, code-review, urgent'"""
        # LLM extracts: title="review code", tags=["work", "code-review", "urgent"]
        params = AddTaskParams(
            user_id=test_user,
            title="review code",
            tags=["work", "code-review", "urgent"]
        )

        result = add_task(session, params)

        assert result.title == "review code"
        assert set(result.tags) == {"work", "code-review", "urgent"}

    def test_no_tags_mentioned(self, session: Session, test_user: str):
        """User says: 'add task write report'"""
        # LLM extracts: title="write report", tags=None (not mentioned)
        params = AddTaskParams(
            user_id=test_user,
            title="write report"
            # No tags parameter
        )

        result = add_task(session, params)

        assert result.title == "write report"
        assert result.tags == []

    def test_tags_with_due_date(self, session: Session, test_user: str):
        """User says: 'add submit proposal due tomorrow, tags: work, deadline'"""
        # LLM extracts: title="submit proposal", due_date="tomorrow", tags=["work", "deadline"]
        params = AddTaskParams(
            user_id=test_user,
            title="submit proposal",
            due_date="tomorrow at 5pm",
            tags=["work", "deadline"]
        )

        result = add_task(session, params)

        assert result.title == "submit proposal"
        assert result.due_date is not None
        assert set(result.tags) == {"work", "deadline"}

    def test_tags_with_priority(self, session: Session, test_user: str):
        """User says: 'add urgent task fix bug, tags: critical, production'"""
        # LLM extracts: title="fix bug", priority="high", tags=["critical", "production"]
        params = AddTaskParams(
            user_id=test_user,
            title="fix bug",
            priority="high",
            tags=["critical", "production"]
        )

        result = add_task(session, params)

        assert result.title == "fix bug"
        assert result.priority == "high"
        assert set(result.tags) == {"critical", "production"}

    def test_mixed_case_tags_from_user(self, session: Session, test_user: str):
        """User says: 'add task with tags Work, URGENT, Shopping'"""
        # LLM might extract as-is: tags=["Work", "URGENT", "Shopping"]
        # MCP tool should normalize
        params = AddTaskParams(
            user_id=test_user,
            title="grocery shopping",
            tags=["Work", "URGENT", "Shopping"]
        )

        result = add_task(session, params)

        # Should be normalized to lowercase
        assert set(result.tags) == {"work", "urgent", "shopping"}

    def test_tags_with_description(self, session: Session, test_user: str):
        """User says: 'add call dentist at 2pm for checkup, tags: health, appointments'"""
        # LLM extracts: title="call dentist", description="at 2pm for checkup", tags=["health", "appointments"]
        params = AddTaskParams(
            user_id=test_user,
            title="call dentist",
            description="at 2pm for checkup",
            tags=["health", "appointments"]
        )

        result = add_task(session, params)

        assert result.title == "call dentist"
        assert result.description == "at 2pm for checkup"
        assert set(result.tags) == {"health", "appointments"}

    def test_overlapping_tag_and_title(self, session: Session, test_user: str):
        """User says: 'add shopping task, tags: shopping, groceries'"""
        # LLM might extract: title="shopping task", tags=["shopping", "groceries"]
        # Both title and tag contain "shopping" - should work fine
        params = AddTaskParams(
            user_id=test_user,
            title="shopping task",
            tags=["shopping", "groceries"]
        )

        result = add_task(session, params)

        assert "shopping" in result.title
        assert "shopping" in result.tags
        assert "groceries" in result.tags


class TestChatbotTagNormalization:
    """Test that tags from chatbot are properly normalized."""

    def test_duplicate_tags_from_parsing(self, session: Session, test_user: str):
        """LLM might extract duplicate tags from user input."""
        # User says: "add task with tags work, urgent, work"
        # LLM extracts: tags=["work", "urgent", "work"]
        params = AddTaskParams(
            user_id=test_user,
            title="team meeting",
            tags=["work", "urgent", "work"]
        )

        result = add_task(session, params)

        # Should deduplicate
        assert set(result.tags) == {"work", "urgent"}
        assert len(result.tags) == 2

    def test_whitespace_in_extracted_tags(self, session: Session, test_user: str):
        """LLM might extract tags with extra whitespace."""
        # Tags extracted with whitespace: ["  work  ", " urgent"]
        params = AddTaskParams(
            user_id=test_user,
            title="project review",
            tags=["  work  ", " urgent", "review "]
        )

        result = add_task(session, params)

        # Should strip whitespace
        assert set(result.tags) == {"work", "urgent", "review"}

    def test_empty_strings_in_tag_list(self, session: Session, test_user: str):
        """LLM might include empty strings if parsing is imperfect."""
        params = AddTaskParams(
            user_id=test_user,
            title="task",
            tags=["work", "", "urgent", "   "]
        )

        result = add_task(session, params)

        # Should filter out empty strings
        assert set(result.tags) == {"work", "urgent"}

    def test_invalid_characters_from_parsing(self, session: Session, test_user: str):
        """LLM might extract tags with invalid characters."""
        # User input might have punctuation: "work!", "urgent?"
        params = AddTaskParams(
            user_id=test_user,
            title="important task",
            tags=["work!", "urgent?", "valid-tag"]
        )

        result = add_task(session, params)

        # Should filter invalid, keep valid
        assert "valid-tag" in result.tags
        # Invalid tags should be filtered
        assert "work!" not in result.tags
        assert "urgent?" not in result.tags


class TestRealWorldScenarios:
    """Test realistic chatbot interaction scenarios."""

    def test_grocery_list_scenario(self, session: Session, test_user: str):
        """User: 'add buy groceries for dinner party, tags: shopping, food, weekend'"""
        params = AddTaskParams(
            user_id=test_user,
            title="buy groceries for dinner party",
            tags=["shopping", "food", "weekend"],
            priority="medium",
            due_date="Saturday"
        )

        result = add_task(session, params)

        assert "groceries" in result.title
        assert set(result.tags) == {"shopping", "food", "weekend"}

    def test_work_deadline_scenario(self, session: Session, test_user: str):
        """User: 'add urgent task submit Q4 report by Friday, tags: work, deadline, report'"""
        params = AddTaskParams(
            user_id=test_user,
            title="submit Q4 report",
            priority="high",
            due_date="Friday at 5pm",
            tags=["work", "deadline", "report"]
        )

        result = add_task(session, params)

        assert result.priority == "high"
        assert result.due_date is not None
        assert set(result.tags) == {"work", "deadline", "report"}

    def test_personal_reminder_scenario(self, session: Session, test_user: str):
        """User: 'remind me to call mom, tags: personal, family'"""
        params = AddTaskParams(
            user_id=test_user,
            title="call mom",
            tags=["personal", "family"],
            priority="low"
        )

        result = add_task(session, params)

        assert result.title == "call mom"
        assert set(result.tags) == {"personal", "family"}

    def test_maintenance_task_scenario(self, session: Session, test_user: str):
        """User: 'add schedule car service next month, tags: car, maintenance, monthly'"""
        params = AddTaskParams(
            user_id=test_user,
            title="schedule car service",
            due_date="next month",
            tags=["car", "maintenance", "monthly"]
        )

        result = add_task(session, params)

        assert "car" in result.title
        assert set(result.tags) == {"car", "maintenance", "monthly"}
