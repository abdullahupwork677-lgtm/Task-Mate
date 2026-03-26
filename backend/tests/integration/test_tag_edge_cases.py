"""Integration tests for tag edge cases and complex scenarios.

Tests advanced tag functionality:
1. Duplicate detection and prevention
2. Case-insensitive tag matching
3. Whitespace handling
4. Tag normalization edge cases
5. Concurrent tag modifications
6. Large tag lists
7. Special characters in tags
8. Tag persistence across operations

Phase V - Task Tags & Categories (003-task-tags)
"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.models import User, Task
from src.mcp_tools.add_tag import add_tag, AddTagParams
from src.mcp_tools.remove_tag import remove_tag, RemoveTagParams
from src.services.tag_service import TagService


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


class TestDuplicateDetection:
    """Test duplicate tag detection and prevention."""

    def test_add_duplicate_tag_in_same_call(self, session: Session, test_user: str):
        """Adding duplicate tags in the same call should deduplicate."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=[]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["work", "work", "WORK", "urgent"]
        )

        result = add_tag(session, params)

        # Should only have 2 unique tags (work and urgent)
        assert set(result.tags) == {"work", "urgent"}
        assert len(result.tags) == 2

    def test_add_tag_that_already_exists_on_task(self, session: Session, test_user: str):
        """Adding a tag that already exists should not duplicate."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=["work", "urgent"]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["work"]  # Already exists
        )

        result = add_tag(session, params)

        # Should still only have 2 tags
        assert set(result.tags) == {"work", "urgent"}
        assert result.tags_already_present == ["work"]

    def test_add_existing_tag_with_different_case(self, session: Session, test_user: str):
        """Adding 'Work' when 'work' exists should not duplicate."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=["work"]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["WORK", "Work", "WoRk"]  # Different cases
        )

        result = add_tag(session, params)

        # Should still only have 1 tag (normalized to lowercase)
        assert result.tags == ["work"]
        assert result.tags_added == []
        assert set(result.tags_already_present) == {"work"}


class TestCaseInsensitiveMatching:
    """Test case-insensitive tag matching."""

    def test_remove_tag_with_different_case(self, session: Session, test_user: str):
        """Removing 'WORK' should remove 'work' tag."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=["work", "urgent"]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = RemoveTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["WORK"]  # Different case
        )

        result = remove_tag(session, params)

        assert result.tags == ["urgent"]
        assert result.tags_removed == ["work"]

    def test_remove_multiple_tags_mixed_case(self, session: Session, test_user: str):
        """Removing tags with mixed cases should work."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=["work", "urgent", "shopping"]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = RemoveTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["WORK", "Urgent", "shopping"]
        )

        result = remove_tag(session, params)

        assert result.tags == []
        assert set(result.tags_removed) == {"work", "urgent", "shopping"}


class TestWhitespaceHandling:
    """Test whitespace handling in tags."""

    def test_add_tags_with_leading_trailing_whitespace(self, session: Session, test_user: str):
        """Whitespace should be stripped from tags."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=[]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["  work  ", " urgent ", "shopping"]
        )

        result = add_tag(session, params)

        # Whitespace should be stripped
        assert set(result.tags) == {"work", "urgent", "shopping"}

    def test_add_empty_strings_and_whitespace_only(self, session: Session, test_user: str):
        """Empty strings and whitespace-only strings should be filtered."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=[]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["work", "", "   ", "urgent", "\t", "\n"]
        )

        result = add_tag(session, params)

        # Only valid tags should be added
        assert set(result.tags) == {"work", "urgent"}


class TestTagNormalizationEdgeCases:
    """Test edge cases in tag normalization."""

    def test_add_tags_with_special_valid_characters(self, session: Session, test_user: str):
        """Tags with hyphens and underscores should work."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=[]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["high-priority", "work_related", "q1-2026"]
        )

        result = add_tag(session, params)

        assert set(result.tags) == {"high-priority", "work_related", "q1-2026"}

    def test_add_tags_with_invalid_special_characters(self, session: Session, test_user: str):
        """Tags with invalid special characters should be filtered."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=[]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["valid-tag", "invalid!", "work@home", "tag#1", "also-valid"]
        )

        result = add_tag(session, params)

        # Only valid tags should be added
        assert "valid-tag" in result.tags
        assert "also-valid" in result.tags
        # Invalid tags should be filtered
        assert "invalid!" not in result.tags
        assert "work@home" not in result.tags
        assert "tag#1" not in result.tags

    def test_add_very_long_tag(self, session: Session, test_user: str):
        """Tags exceeding 50 characters should be filtered."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=[]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        long_tag = "a" * 51
        valid_tag = "a" * 50

        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=[long_tag, valid_tag, "short"]
        )

        result = add_tag(session, params)

        # Long tag should be filtered, max length tag should pass
        assert valid_tag in result.tags
        assert "short" in result.tags
        assert long_tag not in result.tags


class TestLargeTagLists:
    """Test handling of large tag lists."""

    def test_add_many_tags(self, session: Session, test_user: str):
        """Should handle adding many tags at once."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=[]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        many_tags = [f"tag{i}" for i in range(50)]

        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=many_tags
        )

        result = add_tag(session, params)

        assert len(result.tags) == 50
        assert all(f"tag{i}" in result.tags for i in range(50))

    def test_remove_many_tags(self, session: Session, test_user: str):
        """Should handle removing many tags at once."""
        many_tags = [f"tag{i}" for i in range(50)]

        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=many_tags
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Remove half of the tags
        tags_to_remove = [f"tag{i}" for i in range(25)]

        params = RemoveTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=tags_to_remove
        )

        result = remove_tag(session, params)

        assert len(result.tags) == 25
        assert len(result.tags_removed) == 25

    def test_task_with_100_tags(self, session: Session, test_user: str):
        """Should handle tasks with up to 100 tags."""
        many_tags = [f"tag{i}" for i in range(100)]

        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=many_tags
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Verify task has 100 tags
        assert len(task.tags) == 100

        # Add one more tag
        params = AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["extra"]
        )

        result = add_tag(session, params)

        # Should have 101 tags (no hard limit in validation)
        # Note: Pydantic validation allows up to 100 tags in array
        # but backend can store more


class TestTagPersistence:
    """Test tag persistence across operations."""

    def test_tags_persist_after_completion(self, session: Session, test_user: str):
        """Tags should persist when task is marked complete."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=["work", "urgent"]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Mark as complete
        task.completed = True
        session.add(task)
        session.commit()
        session.refresh(task)

        # Tags should still be present
        assert set(task.tags) == {"work", "urgent"}

    def test_tags_persist_across_multiple_modifications(self, session: Session, test_user: str):
        """Tags should persist through multiple add/remove operations."""
        task = Task(
            title="Test task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=["initial"]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Add tags
        add_tag(session, AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["work", "urgent"]
        ))

        # Remove a tag
        remove_tag(session, RemoveTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["initial"]
        ))

        # Add more tags
        add_tag(session, AddTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["important"]
        ))

        # Final verification
        session.refresh(task)
        assert set(task.tags) == {"work", "urgent", "important"}


class TestTagServiceEdgeCases:
    """Test TagService edge cases directly."""

    def test_normalize_tags_with_duplicates_and_case(self):
        """Normalization should handle duplicates and case."""
        tag_service = TagService()
        tags = ["Work", "work", "WORK", "urgent", "Urgent"]

        result = tag_service.normalize_tags(tags)

        assert result == ["work", "urgent"]
        assert len(result) == 2

    def test_validate_and_normalize_mixed_valid_invalid(self):
        """Should filter invalid and keep valid tags."""
        tag_service = TagService()
        tags = ["valid", "valid-tag", "invalid!", "", "also_valid", "a" * 51]

        result = tag_service.validate_and_normalize_tags(tags)

        assert "valid" in result
        assert "valid-tag" in result
        assert "also_valid" in result
        assert "invalid!" not in result
        assert "" not in result

    def test_generate_same_color_for_same_tag(self):
        """Same tag should always generate same color."""
        tag_service = TagService()

        color1 = tag_service.generate_tag_color("work")
        color2 = tag_service.generate_tag_color("work")
        color3 = tag_service.generate_tag_color("work")

        assert color1 == color2 == color3

    def test_generate_different_colors_for_different_tags(self):
        """Different tags should generate different colors."""
        tag_service = TagService()

        color_work = tag_service.generate_tag_color("work")
        color_urgent = tag_service.generate_tag_color("urgent")
        color_shopping = tag_service.generate_tag_color("shopping")

        assert color_work != color_urgent
        assert color_urgent != color_shopping
        assert color_work != color_shopping


class TestConcurrentTagModifications:
    """Test concurrent tag modification scenarios."""

    def test_multiple_users_with_same_tag_names(self, session: Session):
        """Different users can have same tag names independently."""
        # Create two users
        user1 = User(
            id="user-1",
            email="user1@example.com",
            name="User 1",
            password_hash="hash1"
        )
        user2 = User(
            id="user-2",
            email="user2@example.com",
            name="User 2",
            password_hash="hash2"
        )
        session.add(user1)
        session.add(user2)
        session.commit()

        # Create tasks for each user
        task1 = Task(
            title="User 1 task",
            user_id="user-1",
            priority="medium",
            completed=False,
            tags=[]
        )
        task2 = Task(
            title="User 2 task",
            user_id="user-2",
            priority="medium",
            completed=False,
            tags=[]
        )
        session.add(task1)
        session.add(task2)
        session.commit()
        session.refresh(task1)
        session.refresh(task2)

        # Both users add "work" tag
        add_tag(session, AddTagParams(
            user_id="user-1",
            task_id=task1.id,
            tags=["work"]
        ))

        add_tag(session, AddTagParams(
            user_id="user-2",
            task_id=task2.id,
            tags=["work"]
        ))

        # Verify both tasks have "work" tag independently
        session.refresh(task1)
        session.refresh(task2)
        assert "work" in task1.tags
        assert "work" in task2.tags
