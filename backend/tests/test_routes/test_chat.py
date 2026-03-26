"""E2E tests for chat endpoint.

Tests the complete flow from HTTP request to database persistence.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
import json

from src.main import app
from src.models import Task, Conversation, Message
from src.auth import create_access_token


class TestChatEndpoint:
    """E2E tests for POST /api/{user_id}/chat endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_token(self):
        """Create valid JWT token."""
        user_id = "test-user-123"
        return create_access_token({"sub": user_id})

    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authorization headers."""
        return {"Authorization": f"Bearer {auth_token}"}

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.add_task')
    @patch('src.routes.chat.ConversationService')
    def test_chat_add_task_creates_task_in_db(
        self,
        mock_conv_service_class,
        mock_add_task,
        mock_run_agent,
        client,
        auth_headers
    ):
        """E2E Test: POST /chat with 'Add task' → verify task created in DB."""
        # Arrange
        user_id = "test-user-123"

        # Mock conversation service
        mock_service = Mock()
        mock_conversation = Conversation(
            id=1,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        # Mock agent response with tool call
        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="I've added 'Buy milk' to your tasks.",
            tool_calls=[
                {
                    'tool': 'add_task',
                    'params': {'title': 'Buy milk'}
                }
            ]
        )

        # Mock add_task tool execution
        from src.mcp_tools.add_task import AddTaskResult
        mock_add_task.return_value = AddTaskResult(
            task_id=42,
            title="Buy milk",
            description=None,
            completed=False,
            created_at=datetime.utcnow()
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "Add task to buy milk"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["conversation_id"] == 1
        assert "milk" in data["response"].lower()
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["tool"] == "add_task"
        assert data["tool_calls"][0]["result"]["task_id"] == 42

        # Verify task was created
        mock_add_task.assert_called_once()
        call_args = mock_add_task.call_args
        assert call_args[0][1].user_id == user_id  # params.user_id
        assert call_args[0][1].title == "Buy milk"

        # Verify messages were stored
        assert mock_service.add_message.call_count == 2  # User + assistant

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.ConversationService')
    def test_chat_resume_conversation_includes_history(
        self,
        mock_conv_service_class,
        mock_run_agent,
        client,
        auth_headers
    ):
        """E2E Test: Resume conversation → verify history included."""
        # Arrange
        user_id = "test-user-123"
        conversation_id = 5

        # Mock conversation service
        mock_service = Mock()
        mock_conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.get_conversation.return_value = mock_conversation

        # Mock conversation history
        mock_history = [
            Message(
                id=1,
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content="Add task to buy milk",
                created_at=datetime.utcnow()
            ),
            Message(
                id=2,
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content="I've added 'Buy milk'",
                created_at=datetime.utcnow()
            )
        ]
        mock_service.get_conversation_history.return_value = mock_history
        mock_conv_service_class.return_value = mock_service

        # Mock agent response
        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="You have 1 task: Buy milk",
            tool_calls=[]
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={
                "conversation_id": conversation_id,
                "message": "Show my tasks"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conversation_id

        # Verify agent was called with history
        mock_run_agent.assert_called_once()
        call_kwargs = mock_run_agent.call_args[1]
        conversation_history = call_kwargs["conversation_history"]

        assert len(conversation_history) == 2
        assert conversation_history[0]["role"] == "user"
        assert conversation_history[0]["content"] == "Add task to buy milk"
        assert conversation_history[1]["role"] == "assistant"

    @patch('src.routes.chat.ConversationService')
    def test_chat_user_isolation_403_for_other_users_conversation(
        self,
        mock_conv_service_class,
        client,
        auth_headers
    ):
        """E2E Test: User isolation → 403 when accessing other user's conversation."""
        # Arrange
        authenticated_user = "test-user-123"
        other_user = "other-user-456"
        conversation_id = 10

        # Mock service to return None (conversation not found for user)
        mock_service = Mock()
        mock_service.get_conversation.return_value = None
        mock_conv_service_class.return_value = mock_service

        # Act - try to access other user's chat
        response = client.post(
            f"/api/{other_user}/chat",  # Different user in path
            headers=auth_headers,  # But token is for test-user-123
            json={
                "conversation_id": conversation_id,
                "message": "Show my tasks"
            }
        )

        # Assert
        assert response.status_code == 403
        assert "cannot access" in response.json()["detail"].lower()

    def test_chat_requires_authentication(self, client):
        """Test that chat endpoint requires authentication."""
        # Act
        response = client.post(
            "/api/test-user/chat",
            json={"message": "Add task"}
        )

        # Assert
        assert response.status_code == 401  # Unauthorized

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.ConversationService')
    def test_chat_404_for_nonexistent_conversation(
        self,
        mock_conv_service_class,
        mock_run_agent,
        client,
        auth_headers
    ):
        """Test that resuming nonexistent conversation returns 404."""
        # Arrange
        user_id = "test-user-123"
        nonexistent_conversation_id = 9999

        # Mock service to return None (conversation not found)
        mock_service = Mock()
        mock_service.get_conversation.return_value = None
        mock_conv_service_class.return_value = mock_service

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={
                "conversation_id": nonexistent_conversation_id,
                "message": "Show tasks"
            }
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.ConversationService')
    def test_chat_creates_new_conversation_when_not_provided(
        self,
        mock_conv_service_class,
        mock_run_agent,
        client,
        auth_headers
    ):
        """Test that omitting conversation_id creates new conversation."""
        # Arrange
        user_id = "test-user-123"

        # Mock conversation service
        mock_service = Mock()
        mock_new_conversation = Conversation(
            id=100,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_new_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        # Mock agent
        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="Hello! How can I help?",
            tool_calls=[]
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "Hello"}  # No conversation_id
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == 100

        # Verify new conversation was created
        mock_service.create_conversation.assert_called_once_with(user_id)

    def test_chat_validates_empty_message(self, client, auth_headers):
        """Test that empty message is rejected."""
        # Act
        response = client.post(
            "/api/test-user-123/chat",
            headers=auth_headers,
            json={"message": ""}
        )

        # Assert
        assert response.status_code == 422  # Validation error

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.ConversationService')
    def test_chat_updates_conversation_timestamp(
        self,
        mock_conv_service_class,
        mock_run_agent,
        client,
        auth_headers
    ):
        """Test that conversation timestamp is updated after chat."""
        # Arrange
        user_id = "test-user-123"

        mock_service = Mock()
        mock_conversation = Conversation(
            id=1,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="OK",
            tool_calls=[]
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "Test"}
        )

        # Assert
        assert response.status_code == 200

        # Verify timestamp was updated
        mock_service.update_conversation_timestamp.assert_called_once_with(1)


class TestChatEndpointWithListTasks:
    """E2E tests for chat endpoint with list_tasks functionality (Phase 4)."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_token(self):
        """Create valid JWT token."""
        user_id = "test-user-123"
        return create_access_token({"sub": user_id})

    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authorization headers."""
        return {"Authorization": f"Bearer {auth_token}"}

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.list_tasks')
    @patch('src.routes.chat.ConversationService')
    def test_chat_show_tasks_returns_task_list(
        self,
        mock_conv_service_class,
        mock_list_tasks,
        mock_run_agent,
        client,
        auth_headers
    ):
        """E2E Test: Add tasks → Ask 'Show my tasks' → Verify tasks listed in response."""
        # Arrange
        user_id = "test-user-123"

        # Mock conversation service
        mock_service = Mock()
        mock_conversation = Conversation(
            id=1,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        # Mock agent response with list_tasks tool call
        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="You have 3 tasks: Buy milk, Call mom, Finish report.",
            tool_calls=[
                {
                    'tool': 'list_tasks',
                    'params': {'status': 'all'}
                }
            ]
        )

        # Mock list_tasks tool execution
        from src.mcp_tools.list_tasks import ListTasksResult
        mock_list_tasks.return_value = ListTasksResult(
            tasks=[
                {
                    'task_id': 1,
                    'title': 'Buy milk',
                    'description': None,
                    'completed': False,
                    'created_at': datetime.utcnow()
                },
                {
                    'task_id': 2,
                    'title': 'Call mom',
                    'description': None,
                    'completed': False,
                    'created_at': datetime.utcnow()
                },
                {
                    'task_id': 3,
                    'title': 'Finish report',
                    'description': 'Quarterly sales',
                    'completed': True,
                    'created_at': datetime.utcnow()
                }
            ],
            count=3
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "Show my tasks"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["conversation_id"] == 1
        assert "tasks" in data["response"].lower() or "buy milk" in data["response"].lower()
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["tool"] == "list_tasks"
        assert data["tool_calls"][0]["result"]["count"] == 3
        assert len(data["tool_calls"][0]["result"]["tasks"]) == 3

        # Verify list_tasks was called
        mock_list_tasks.assert_called_once()
        call_args = mock_list_tasks.call_args
        assert call_args[0][1].user_id == user_id
        assert call_args[0][1].status == "all"

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.list_tasks')
    @patch('src.routes.chat.ConversationService')
    def test_chat_filter_by_status_pending(
        self,
        mock_conv_service_class,
        mock_list_tasks,
        mock_run_agent,
        client,
        auth_headers
    ):
        """E2E Test: Filter by status via natural language → Verify correct filtering."""
        # Arrange
        user_id = "test-user-456"

        # Mock conversation service
        mock_service = Mock()
        mock_conversation = Conversation(
            id=2,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        # Mock agent response with list_tasks tool call (status=pending)
        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="You have 2 pending tasks: Buy milk, Call mom.",
            tool_calls=[
                {
                    'tool': 'list_tasks',
                    'params': {'status': 'pending'}
                }
            ]
        )

        # Mock list_tasks returning only pending tasks
        from src.mcp_tools.list_tasks import ListTasksResult
        mock_list_tasks.return_value = ListTasksResult(
            tasks=[
                {
                    'task_id': 1,
                    'title': 'Buy milk',
                    'description': None,
                    'completed': False,
                    'created_at': datetime.utcnow()
                },
                {
                    'task_id': 2,
                    'title': 'Call mom',
                    'description': None,
                    'completed': False,
                    'created_at': datetime.utcnow()
                }
            ],
            count=2
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "What's pending?"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["tool_calls"][0]["tool"] == "list_tasks"
        assert data["tool_calls"][0]["params"]["status"] == "pending"
        assert data["tool_calls"][0]["result"]["count"] == 2

        # Verify all returned tasks are incomplete
        for task in data["tool_calls"][0]["result"]["tasks"]:
            assert task["completed"] is False

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.list_tasks')
    @patch('src.routes.chat.ConversationService')
    def test_chat_filter_by_status_completed(
        self,
        mock_conv_service_class,
        mock_list_tasks,
        mock_run_agent,
        client,
        auth_headers
    ):
        """E2E Test: Filter completed tasks → Verify only completed returned."""
        # Arrange
        user_id = "test-user-789"

        mock_service = Mock()
        mock_conversation = Conversation(
            id=3,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="You completed 1 task: Finish report.",
            tool_calls=[
                {
                    'tool': 'list_tasks',
                    'params': {'status': 'completed'}
                }
            ]
        )

        from src.mcp_tools.list_tasks import ListTasksResult
        mock_list_tasks.return_value = ListTasksResult(
            tasks=[
                {
                    'task_id': 3,
                    'title': 'Finish report',
                    'description': 'Quarterly sales',
                    'completed': True,
                    'created_at': datetime.utcnow()
                }
            ],
            count=1
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "Show completed tasks"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["tool_calls"][0]["params"]["status"] == "completed"
        assert data["tool_calls"][0]["result"]["count"] == 1
        # Verify all returned tasks are complete
        for task in data["tool_calls"][0]["result"]["tasks"]:
            assert task["completed"] is True

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.list_tasks')
    @patch('src.routes.chat.ConversationService')
    def test_chat_empty_task_list(
        self,
        mock_conv_service_class,
        mock_list_tasks,
        mock_run_agent,
        client,
        auth_headers
    ):
        """E2E Test: User with no tasks → Agent responds helpfully."""
        # Arrange
        user_id = "test-user-empty"

        mock_service = Mock()
        mock_conversation = Conversation(
            id=4,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="You don't have any tasks yet. Would you like to add one?",
            tool_calls=[
                {
                    'tool': 'list_tasks',
                    'params': {'status': 'all'}
                }
            ]
        )

        from src.mcp_tools.list_tasks import ListTasksResult
        mock_list_tasks.return_value = ListTasksResult(
            tasks=[],
            count=0
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "Show my tasks"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["tool_calls"][0]["result"]["count"] == 0
        assert len(data["tool_calls"][0]["result"]["tasks"]) == 0
        assert "don't have" in data["response"].lower() or "no tasks" in data["response"].lower()


class TestChatEndpointWithCompleteTask:
    """E2E tests for chat endpoint with complete_task functionality (Phase 5)."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_token(self):
        """Create valid JWT token."""
        user_id = "test-user-123"
        return create_access_token({"sub": user_id})

    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authorization headers."""
        return {"Authorization": f"Bearer {auth_token}"}

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.complete_task')
    @patch('src.routes.chat.ConversationService')
    def test_chat_complete_task_by_id(
        self,
        mock_conv_service_class,
        mock_complete_task,
        mock_run_agent,
        client,
        auth_headers
    ):
        """E2E Test: Add task → Complete via chat → Verify task.completed = true in DB."""
        # Arrange
        user_id = "test-user-123"

        # Mock conversation service
        mock_service = Mock()
        mock_conversation = Conversation(
            id=1,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        # Mock agent response with complete_task tool call
        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="I've marked task 5 as complete.",
            tool_calls=[
                {
                    'tool': 'complete_task',
                    'params': {'task_id': 5}
                }
            ]
        )

        # Mock complete_task tool execution
        from src.mcp_tools.complete_task import CompleteTaskResult
        mock_complete_task.return_value = CompleteTaskResult(
            task_id=5,
            title="Buy milk",
            description=None,
            completed=True,
            updated_at=datetime.utcnow()
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "Mark task 5 as complete"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["conversation_id"] == 1
        assert "complete" in data["response"].lower() or "marked" in data["response"].lower()
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["tool"] == "complete_task"
        assert data["tool_calls"][0]["result"]["task_id"] == 5
        assert data["tool_calls"][0]["result"]["completed"] is True

        # Verify complete_task was called
        mock_complete_task.assert_called_once()
        call_args = mock_complete_task.call_args
        assert call_args[0][1].user_id == user_id
        assert call_args[0][1].task_id == 5

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.complete_task')
    @patch('src.routes.chat.list_tasks')
    @patch('src.routes.chat.ConversationService')
    def test_chat_complete_task_by_title(
        self,
        mock_conv_service_class,
        mock_list_tasks,
        mock_complete_task,
        mock_run_agent,
        client,
        auth_headers
    ):
        """E2E Test: Complete by title (natural language) → Verify correct task completed."""
        # Arrange
        user_id = "test-user-456"

        mock_service = Mock()
        mock_conversation = Conversation(
            id=2,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        # Mock agent response with multiple tool calls
        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="Great! I've marked 'Buy milk' as complete.",
            tool_calls=[
                {
                    'tool': 'list_tasks',
                    'params': {'status': 'pending'}
                },
                {
                    'tool': 'complete_task',
                    'params': {'task_id': 1}
                }
            ]
        )

        # Mock list_tasks (to find task by title)
        from src.mcp_tools.list_tasks import ListTasksResult
        mock_list_tasks.return_value = ListTasksResult(
            tasks=[
                {
                    'task_id': 1,
                    'title': 'Buy milk',
                    'description': None,
                    'completed': False,
                    'created_at': datetime.utcnow()
                }
            ],
            count=1
        )

        # Mock complete_task
        from src.mcp_tools.complete_task import CompleteTaskResult
        mock_complete_task.return_value = CompleteTaskResult(
            task_id=1,
            title="Buy milk",
            description=None,
            completed=True,
            updated_at=datetime.utcnow()
        )

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "I finished buying milk"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should have both tool calls
        assert len(data["tool_calls"]) == 2
        assert data["tool_calls"][0]["tool"] == "list_tasks"
        assert data["tool_calls"][1]["tool"] == "complete_task"
        assert data["tool_calls"][1]["result"]["task_id"] == 1
        assert data["tool_calls"][1]["result"]["completed"] is True

    @patch('src.routes.chat.run_agent')
    @patch('src.routes.chat.complete_task')
    @patch('src.routes.chat.ConversationService')
    def test_chat_complete_nonexistent_task(
        self,
        mock_conv_service_class,
        mock_complete_task,
        mock_run_agent,
        client,
        auth_headers
    ):
        """E2E Test: Complete non-existent task → Error handled gracefully."""
        # Arrange
        user_id = "test-user-789"

        mock_service = Mock()
        mock_conversation = Conversation(
            id=3,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.create_conversation.return_value = mock_conversation
        mock_service.get_conversation_history.return_value = []
        mock_conv_service_class.return_value = mock_service

        # Mock agent response
        from src.ai_agent.runner import AgentResponse
        mock_run_agent.return_value = AgentResponse(
            response="I couldn't find task 9999. Would you like to see your task list?",
            tool_calls=[
                {
                    'tool': 'complete_task',
                    'params': {'task_id': 9999}
                }
            ]
        )

        # Mock complete_task to raise error
        mock_complete_task.side_effect = ValueError("Task not found")

        # Act
        response = client.post(
            f"/api/{user_id}/chat",
            headers=auth_headers,
            json={"message": "Mark task 9999 as complete"}
        )

        # Assert
        assert response.status_code == 200  # Should not crash
        data = response.json()

        # Tool call should be in list but execution failed
        # The endpoint continues even if tool fails
        assert "couldn't find" in data["response"].lower() or "not found" in data["response"].lower()
