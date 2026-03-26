"""Chat API Routes.

Provides stateless chat endpoint for AI-powered task management conversations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..auth.dependencies import get_current_user
from ..db import get_session
from ..services.conversation_service import ConversationService
from ..ai_agent.runner import run_agent, AgentResponse
from ..ai_agent.tools import register_tools
from ..ai_agent.intent_detector import detect_user_intent
from ..ai_agent.utils import parse_natural_date
from ..ai_agent.context_manager import ContextManager
from ..mcp_tools.add_task import add_task, AddTaskParams
from ..mcp_tools.list_tasks import list_tasks, ListTasksParams
from ..mcp_tools.complete_task import complete_task, CompleteTaskParams
from ..mcp_tools.update_task import update_task, UpdateTaskParams
from ..mcp_tools.delete_task import delete_task, DeleteTaskParams
from ..mcp_tools.find_task import find_task, FindTaskParams
from ..mcp_tools.set_reminder import set_reminder, SetReminderParams
from ..utils.performance import log_execution_time, track_performance
import logging
import json
import time
import re

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.get("/conversations/latest")
async def get_latest_conversation(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get user's most recent conversation with messages.

    Args:
        current_user_id: Authenticated user ID from JWT
        db: Database session

    Returns:
        Latest conversation with its messages, or null if no conversations exist

    Example:
        >>> # GET /api/conversations/latest
        >>> {
        ...     "conversation_id": 5,
        ...     "created_at": "2026-01-01T10:00:00",
        ...     "messages": [...]
        ... }
    """
    try:
        from ..models import Conversation
        from sqlmodel import select, desc

        # Get user's most recent conversation
        statement = (
            select(Conversation)
            .where(Conversation.user_id == current_user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(1)
        )
        conversation = db.exec(statement).first()

        if not conversation:
            return {"conversation_id": None, "messages": []}

        # Fetch messages for this conversation
        conversation_service = ConversationService(db)
        messages = conversation_service.get_conversation_history(
            conversation.id,
            current_user_id,
            limit=100
        )

        return {
            "conversation_id": conversation.id,
            "created_at": conversation.created_at.isoformat() + "Z",  # Add Z for UTC
            "updated_at": conversation.updated_at.isoformat() + "Z",
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() + "Z"  # Add Z for UTC
                }
                for msg in messages
            ]
        }

    except Exception as e:
        logger.error(
            f"Failed to fetch latest conversation: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch latest conversation"
        )


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get all messages for a conversation.

    Args:
        conversation_id: ID of the conversation
        current_user_id: Authenticated user ID from JWT
        db: Database session

    Returns:
        List of messages with role, content, and timestamp

    Raises:
        HTTPException 403: If conversation doesn't belong to user
        HTTPException 404: If conversation not found
    """
    try:
        conversation_service = ConversationService(db)

        # Get conversation to verify ownership
        conversation = conversation_service.get_conversation(
            conversation_id,
            current_user_id
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )

        # Fetch messages
        messages = conversation_service.get_conversation_history(
            conversation_id,
            current_user_id,
            limit=100
        )

        return {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() + "Z"  # Add Z for UTC
                }
                for msg in messages
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to fetch conversation messages: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversation history"
        )


class ChatRequest(BaseModel):
    """Request body for chat endpoint.

    Attributes:
        conversation_id: Optional ID to resume existing conversation
        message: User's message
    """

    conversation_id: Optional[int] = Field(
        None,
        description="Conversation ID to resume (omit for new conversation)"
    )
    message: str = Field(
        ...,
        min_length=1,
        description="User's message"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "message": "Add task to buy milk"
            }
        }


class ChatResponse(BaseModel):
    """Response from chat endpoint.

    Attributes:
        conversation_id: ID of the conversation
        response: Assistant's natural language response
        tool_calls: List of tool calls made by the agent
    """

    conversation_id: int = Field(..., description="Conversation ID")
    response: str = Field(..., description="Assistant's response")
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tool calls made during this turn"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "conversation_id": 42,
                "response": "I've added 'Buy milk' to your tasks.",
                "tool_calls": [
                    {
                        "tool": "add_task",
                        "params": {"title": "Buy milk"}
                    }
                ]
            }
        }


@router.post("/{user_id}/chat", response_model=ChatResponse)
@log_execution_time("chat_endpoint")
async def chat(
    user_id: str,
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> ChatResponse:
    """Process chat message and return AI assistant response.

    This endpoint:
    1. Validates user authentication and authorization
    2. Creates or resumes conversation
    3. Fetches conversation history
    4. Runs AI agent with user message
    5. Executes any tool calls (e.g., add_task)
    6. Stores messages in database
    7. Returns response with conversation context

    Args:
        user_id: User ID from URL path
        request: Chat request with message and optional conversation_id
        current_user_id: Authenticated user ID from JWT
        db: Database session

    Returns:
        ChatResponse with assistant's response and metadata

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If path user_id doesn't match JWT user_id
        HTTPException 404: If conversation_id not found for user
        HTTPException 500: If internal error occurs

    Example:
        >>> # POST /api/user-123/chat
        >>> {
        ...     "message": "Add task to buy milk"
        ... }
        >>> # Response:
        >>> {
        ...     "conversation_id": 1,
        ...     "response": "I've added 'Buy milk' to your tasks.",
        ...     "tool_calls": [{"tool": "add_task", "params": {...}}]
        ... }
    """
    try:
        # Input sanitization (T181) - strip excessive whitespace, limit message length
        sanitized_message = request.message.strip()
        if len(sanitized_message) > 10000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message too long (max 10000 characters)"
            )
        request.message = sanitized_message

        # Structured logging with request context (T170)
        logger.info(
            "Chat request received",
            extra={
                "user_id": user_id,
                "conversation_id": request.conversation_id,
                "message_length": len(request.message),
                "has_conversation_id": request.conversation_id is not None
            }
        )

        # Validate path user_id matches JWT user_id (T060)
        if user_id != current_user_id:
            logger.warning(
                f"User isolation violation: path user_id={user_id}, "
                f"JWT user_id={current_user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access chat for other users"
            )

        # Initialize conversation service
        conversation_service = ConversationService(db)

        # Create or resume conversation (T062)
        if request.conversation_id:
            # Resume existing conversation
            conversation = conversation_service.get_conversation(
                request.conversation_id,
                user_id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {request.conversation_id} not found"
                )
            conversation_id = conversation.id
        else:
            # Create new conversation
            conversation = conversation_service.create_conversation(user_id)
            conversation_id = conversation.id

        logger.info(
            f"Processing chat for user {user_id}, "
            f"conversation {conversation_id}"
        )

        # Fetch conversation history (last 50 messages) (T063)
        history_messages = conversation_service.get_conversation_history(
            conversation_id,
            user_id,
            limit=50
        )

        # Convert to format expected by agent + intent detector.
        # Include tool_calls for better follow-up/confirmation handling.
        conversation_history = [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": getattr(msg, "tool_calls", None),
            }
            for msg in history_messages
        ]

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # ADDING_TASK STATE MANAGEMENT - MULTI-TURN WORKFLOW
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Check if we're in ADDING_TASK workflow
        # If yes, handle multi-turn conversation: confirm → priority → deadline → description → create

        context_manager = ContextManager(conversation_service)
        current_state = context_manager.get_current_state(conversation_id, user_id)

        if current_state and current_state.get('current_intent') == 'ADDING_TASK':
            logger.info(
                f"User in ADDING_TASK workflow: step={current_state.get('state_data', {}).get('step')}",
                extra={"user_id": user_id, "conversation_id": conversation_id, "state": current_state}
            )

            # Collect information for current step
            state_data = current_state.get('state_data', {})
            updated_state, next_step = context_manager.collect_add_task_information(
                conversation_id=conversation_id,
                user_id=user_id,
                user_message=request.message,
                current_state=state_data
            )

            # Handle cancellation
            if next_step == "cancel":
                context_manager.reset_state_after_completion(conversation_id, user_id)
                cancel_msg = "❌ Add task cancelled. No task was created."

                conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="user",
                    content=request.message
                )
                conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="assistant",
                    content=cancel_msg
                )
                conversation_service.update_conversation_timestamp(conversation_id)

                return ChatResponse(
                    conversation_id=conversation_id,
                    response=cancel_msg,
                    tool_calls=[]
                )

            # Handle intent switching
            if next_step == "switch_intent":
                context_manager.reset_state_after_completion(conversation_id, user_id)
                # Continue to normal intent detection below

            # Handle task creation
            elif next_step == "create":
                # All information collected, create the task
                logger.info(
                    f"Creating task with collected information",
                    extra={"user_id": user_id, "state_data": updated_state}
                )

                # T029: Validate state_data completeness before creating task
                title = updated_state.get("title")
                if not title or not title.strip():
                    error_msg = "❌ Cannot create task: title is required"
                    logger.error(
                        "Task creation failed - missing title",
                        extra={"user_id": user_id, "state_data": updated_state}
                    )

                    conversation_service.add_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role="user",
                        content=request.message
                    )
                    conversation_service.add_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role="assistant",
                        content=error_msg
                    )
                    conversation_service.update_conversation_timestamp(conversation_id)

                    # Reset state
                    context_manager.reset_state_after_completion(conversation_id, user_id)

                    return ChatResponse(
                        conversation_id=conversation_id,
                        response=error_msg,
                        tool_calls=[]
                    )

                # Build add_task params from state_data
                add_params = {
                    "title": title.strip()
                }

                # Add optional fields if present
                if "priority" in updated_state:
                    add_params["priority"] = updated_state["priority"]
                # Due date is stored as "due_date_parsed" (ISO format) by context_manager
                if "due_date_parsed" in updated_state and updated_state["due_date_parsed"]:
                    add_params["due_date"] = updated_state["due_date_parsed"]
                if "description" in updated_state:
                    add_params["description"] = updated_state["description"]

                # Force add_task execution
                try:
                    params = AddTaskParams(
                        user_id=user_id,
                        **add_params
                    )
                    result = add_task(db, params)

                    # Reset state to NEUTRAL
                    context_manager.reset_state_after_completion(conversation_id, user_id)

                    # Generate success message
                    success_msg = f"✅ Task created successfully! Task #{result.task_id}: {result.title}"
                    if result.priority:
                        success_msg += f" ({result.priority} priority)"
                    if result.due_date:
                        success_msg += f", due {result.due_date.strftime('%B %d, %Y')}"

                    # Store messages
                    conversation_service.add_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role="user",
                        content=request.message
                    )
                    conversation_service.add_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role="assistant",
                        content=success_msg
                    )
                    conversation_service.update_conversation_timestamp(conversation_id)

                    logger.info(
                        f"Task created via multi-turn workflow: task_id={result.task_id}",
                        extra={"user_id": user_id, "task_id": result.task_id}
                    )

                    return ChatResponse(
                        conversation_id=conversation_id,
                        response=success_msg,
                        tool_calls=[{
                            'tool': 'add_task',
                            'params': add_params,
                            'result': {
                                'task_id': result.task_id,
                                'title': result.title,
                                'description': result.description,
                                'priority': result.priority,
                                'due_date': result.due_date.isoformat() if result.due_date else None,
                                'completed': result.completed,
                                'created_at': result.created_at.isoformat()
                            }
                        }]
                    )
                except Exception as e:
                    logger.error(f"Failed to create task in workflow: {e}", exc_info=True)
                    error_msg = f"❌ Failed to create task: {str(e)}"

                    conversation_service.add_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role="user",
                        content=request.message
                    )
                    conversation_service.add_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role="assistant",
                        content=error_msg
                    )
                    conversation_service.update_conversation_timestamp(conversation_id)

                    return ChatResponse(
                        conversation_id=conversation_id,
                        response=error_msg,
                        tool_calls=[]
                    )

            else:
                # Continue workflow - generate prompt for next step
                if next_step == "confirm":
                    prompt_msg = f"Would you like to add the task: '{updated_state.get('title')}'? Reply 'yes' to continue or 'no' to cancel."
                elif next_step == "priority":
                    prompt_msg = "What priority should this task have? (high, medium, or low)"
                elif next_step == "deadline":
                    prompt_msg = "Would you like to set a deadline for this task? (e.g., 'tomorrow', 'next Friday', 'Jan 20', or 'no' to skip)"
                elif next_step == "description":
                    prompt_msg = "Would you like to add a description for this task? (Enter the description or 'no' to skip)"
                else:
                    prompt_msg = "Please continue..."

                # Store messages
                conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="user",
                    content=request.message
                )
                conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="assistant",
                    content=prompt_msg
                )
                conversation_service.update_conversation_timestamp(conversation_id)

                return ChatResponse(
                    conversation_id=conversation_id,
                    response=prompt_msg,
                    tool_calls=[]
                )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # INTENT DETECTION MIDDLEWARE - FORCED TOOL EXECUTION
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Detect user intent BEFORE calling AI agent
        # If intent detected with params, FORCE tool execution
        # This bypasses unreliable AI system prompt interpretation

        detected_intent = detect_user_intent(request.message, conversation_history)
        forced_tool_calls = []

        # Handle explicit cancellation (user said "no" to confirmation)
        if detected_intent is None:
            # Check if last assistant message was asking for confirmation
            if conversation_history:
                last_assistant_msg = None
                for msg in reversed(conversation_history[-3:]):
                    if msg.get('role') == 'assistant':
                        last_assistant_msg = msg.get('content', '').lower()
                        break
                
                # If assistant was asking for confirmation and user said "no", handle cancellation
                if last_assistant_msg and ('sure' in last_assistant_msg or 'confirm' in last_assistant_msg or 'cancel' in last_assistant_msg):
                    message_lower = request.message.lower().strip()
                    is_no = any(keyword in message_lower for keyword in ['no', 'nahi', 'cancel', 'na', 'nope', 'not'])
                    if is_no and len(message_lower.split()) <= 3:  # Short message like "no", "nahi", "cancel"
                        # Determine operation type from assistant's message
                        operation_type = "update"  # default
                        if 'delete' in last_assistant_msg or '🗑️' in last_assistant_msg:
                            operation_type = "delete"
                        elif 'add' in last_assistant_msg or 'create' in last_assistant_msg or '➕' in last_assistant_msg or '📝' in last_assistant_msg and 'task' in last_assistant_msg.lower() and 'add' in last_assistant_msg.lower():
                            operation_type = "add"
                        elif 'complete' in last_assistant_msg or '✅' in last_assistant_msg:
                            operation_type = "complete"
                        elif 'incomplete' in last_assistant_msg or '⏳' in last_assistant_msg:
                            operation_type = "incomplete"
                        elif 'update' in last_assistant_msg or '📝' in last_assistant_msg:
                            operation_type = "update"
                        
                        # Generate operation-specific cancellation message
                        if operation_type == "delete":
                            cancellation_msg = "❌ Deletion cancelled. No task was deleted."
                        elif operation_type == "add":
                            cancellation_msg = "❌ Add task cancelled. No task was created."
                        elif operation_type == "complete":
                            cancellation_msg = "❌ Completion cancelled. Task status unchanged."
                        elif operation_type == "incomplete":
                            cancellation_msg = "❌ Status change cancelled. Task status unchanged."
                        else:
                            cancellation_msg = "❌ Update cancelled. No changes were made."
                        
                        conversation_service.add_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            role="user",
                            content=request.message
                        )
                        conversation_service.add_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            role="assistant",
                            content=cancellation_msg
                        )
                        conversation_service.update_conversation_timestamp(conversation_id)
                        
                        return ChatResponse(
                            conversation_id=conversation_id,
                            response=cancellation_msg,
                            tool_calls=[]
                        )

        if detected_intent:
            logger.info(
                f"Intent detected: {detected_intent}",
                extra={"user_id": user_id, "intent": str(detected_intent), "operation": detected_intent.operation}
            )

            # Check if confirmation is needed
            # If needs_confirmation=True, BYPASS AI and ask confirmation ourselves
            # If needs_confirmation=False, execute tool immediately
            if detected_intent.needs_confirmation:
                logger.info(
                    f"Intent needs confirmation - generating confirmation question",
                    extra={"user_id": user_id, "operation": detected_intent.operation}
                )

                # BYPASS AI AGENT - Generate confirmation question ourselves
                # First, get task details if we have task_id or task_title
                task_details = ""
                if detected_intent.task_id:
                    task_details = f" #{detected_intent.task_id}"
                elif detected_intent.task_title:
                    # Try to find task by title to get ID for better message + context extraction
                    task_details = f" '{detected_intent.task_title}'"
                    try:
                        find_params = FindTaskParams(
                            user_id=user_id,
                            title=detected_intent.task_title
                        )
                        find_result = find_task(db, find_params)
                        if find_result:
                            task_details = f" #{find_result.task_id} ('{find_result.title}')"
                    except:
                        pass

                # Generate confirmation message based on operation
                if detected_intent.operation == "delete":
                    confirmation_msg = f"🗑️ Kya aap sure hain k task{task_details} delete karna hai? (Are you sure you want to delete this task?)\n\nReply 'yes' to confirm or 'no' to cancel."
                elif detected_intent.operation == "complete":
                    # Handle both ID and title for complete
                    if not task_details:
                        if detected_intent.task_id:
                            task_details = f" #{detected_intent.task_id}"
                        elif detected_intent.task_title:
                            task_details = f" '{detected_intent.task_title}'"
                            # Try to find task by title
                            try:
                                find_params = FindTaskParams(
                                    user_id=user_id,
                                    title=detected_intent.task_title
                                )
                                find_result = find_task(db, find_params)
                                if find_result:
                                    task_details = f" '{find_result.title}' (#{find_result.task_id})"
                            except:
                                pass
                    confirmation_msg = f"✅ Task{task_details} ko complete mark kar doon? (Mark this task as complete?)\n\nReply 'yes' to confirm or 'no' to cancel."
                elif detected_intent.operation == "incomplete":
                    # Handle both ID and title for incomplete
                    if not task_details:
                        if detected_intent.task_id:
                            task_details = f" #{detected_intent.task_id}"
                        elif detected_intent.task_title:
                            task_details = f" '{detected_intent.task_title}'"
                            # Try to find task by title
                            try:
                                find_params = FindTaskParams(
                                    user_id=user_id,
                                    title=detected_intent.task_title
                                )
                                find_result = find_task(db, find_params)
                                if find_result:
                                    task_details = f" '{find_result.title}' (#{find_result.task_id})"
                            except:
                                pass
                    confirmation_msg = f"⏳ Task{task_details} ko incomplete mark kar doon? (Mark this task as incomplete?)\n\nReply 'yes' to confirm or 'no' to cancel."
                elif detected_intent.operation == "update":
                    # Summarize intended changes for explicit confirmation
                    changes = []
                    if detected_intent.params:
                        if 'title' in detected_intent.params and detected_intent.params.get('title') is not None:
                            changes.append(f"Title → {detected_intent.params.get('title')}")
                        if 'priority' in detected_intent.params and detected_intent.params.get('priority') is not None:
                            changes.append(f"Priority → {detected_intent.params.get('priority')}")
                        if 'due_date' in detected_intent.params:
                            if detected_intent.params.get('due_date') is None:
                                changes.append("Due date → removed")
                            else:
                                changes.append(f"Due date → {detected_intent.params.get('due_date')}")
                        if 'description' in detected_intent.params and detected_intent.params.get('description') is not None:
                            changes.append("Description → updated")
                        if 'completed' in detected_intent.params and detected_intent.params.get('completed') is not None:
                            changes.append(f"Completed → {detected_intent.params.get('completed')}")
                    change_text = "\n".join([f"• {c}" for c in changes]) if changes else "• (no changes detected)"
                    confirmation_msg = (
                        f"📝 Update Task{task_details} with these changes?\n\n"
                        f"{change_text}\n\n"
                        f"Reply 'yes' to confirm or 'no' to cancel."
                    )
                elif detected_intent.operation == "update_ask":
                    # User wants to update but didn't provide task or details - ask which task first
                    if not detected_intent.task_id and not detected_intent.task_title:
                        # No task specified - ask which task to update
                        list_params = ListTasksParams(user_id=user_id, status="all")
                        list_result = list_tasks(db, list_params)
                        if list_result.tasks:
                            task_list = "\n".join([f"  • #{t['task_id']}: {t['title']}" for t in list_result.tasks[:10]])
                            confirmation_msg = (
                                f"📝 Kaunsa task update karna hai? (Which task would you like to update?)\n\n"
                                f"Here are your current tasks:\n{task_list}\n\n"
                                f"Please specify the task by ID (e.g., #70) or title (e.g., 'buy groceries')."
                            )
                        else:
                            confirmation_msg = (
                                f"📝 Kaunsa task update karna hai? (Which task would you like to update?)\n\n"
                                f"You don't have any tasks to update."
                            )
                    else:
                        # Task specified but no update details - ask what to update
                        # Ensure task details include explicit "Task #id" when possible for context extraction
                        if not task_details and detected_intent.task_title:
                            task_details = f" '{detected_intent.task_title}'"
                        elif not task_details and detected_intent.task_id:
                            task_details = f" #{detected_intent.task_id}"
                        confirmation_msg = (
                            f"📝 Task{task_details} — what would you like to update?\n\n"
                            f"You can reply like:\n"
                            f"• title to Buy groceries\n"
                            f"• priority to high\n"
                            f"• due date to Jan 20, 2026 3 PM\n"
                            f"• remove due date\n"
                            f"• description: ...\n"
                            f"• mark as complete / mark as incomplete\n\n"
                            f"Tell me the changes, then I'll confirm and apply them."
                        )
                elif detected_intent.operation == "delete_ask":
                    # User wants to delete but didn't specify which task - ask which task
                    list_params = ListTasksParams(user_id=user_id, status="all")
                    list_result = list_tasks(db, list_params)
                    if list_result.tasks:
                        task_list = "\n".join([f"  • #{t['task_id']}: {t['title']}" for t in list_result.tasks[:10]])
                        confirmation_msg = (
                            f"🗑️ Kaunsa task delete karna hai? (Which task would you like to delete?)\n\n"
                            f"Here are your current tasks:\n{task_list}\n\n"
                            f"Please specify the task by ID (e.g., #70) or title (e.g., 'buy groceries')."
                        )
                    else:
                        confirmation_msg = (
                            f"🗑️ Kaunsa task delete karna hai? (Which task would you like to delete?)\n\n"
                            f"You don't have any tasks to delete."
                        )
                elif detected_intent.operation == "complete_ask":
                    # User wants to complete but didn't specify which task - ask which task
                    list_params = ListTasksParams(user_id=user_id, status="all")
                    list_result = list_tasks(db, list_params)
                    if list_result.tasks:
                        task_list = "\n".join([f"  • #{t['task_id']}: {t['title']}" for t in list_result.tasks[:10]])
                        confirmation_msg = (
                            f"✅ Kaunsa task complete mark karna hai? (Which task would you like to mark as complete?)\n\n"
                            f"Here are your current tasks:\n{task_list}\n\n"
                            f"Please specify the task by ID (e.g., #70) or title (e.g., 'buy groceries')."
                        )
                    else:
                        confirmation_msg = (
                            f"✅ Kaunsa task complete mark karna hai? (Which task would you like to mark as complete?)\n\n"
                            f"You don't have any tasks to update."
                        )
                elif detected_intent.operation == "incomplete_ask":
                    # User wants to mark incomplete but didn't specify which task - ask which task
                    list_params = ListTasksParams(user_id=user_id, status="all")
                    list_result = list_tasks(db, list_params)
                    if list_result.tasks:
                        task_list = "\n".join([f"  • #{t['task_id']}: {t['title']}" for t in list_result.tasks[:10]])
                        confirmation_msg = (
                            f"⏳ Kaunsa task incomplete mark karna hai? (Which task would you like to mark as incomplete?)\n\n"
                            f"Here are your current tasks:\n{task_list}\n\n"
                            f"Please specify the task by ID (e.g., #70) or title (e.g., 'buy groceries')."
                        )
                    else:
                        confirmation_msg = (
                            f"⏳ Kaunsa task incomplete mark karna hai? (Which task would you like to mark as incomplete?)\n\n"
                            f"You don't have any tasks to update."
                        )
                else:
                    confirmation_msg = "Kya aap sure hain? (Are you sure?)\n\nReply 'yes' to confirm or 'no' to cancel."

                # Store messages in database
                conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="user",
                    content=request.message
                )
                conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="assistant",
                    content=confirmation_msg
                )
                conversation_service.update_conversation_timestamp(conversation_id)

                # Return confirmation question immediately WITHOUT calling AI
                return ChatResponse(
                    conversation_id=conversation_id,
                    response=confirmation_msg,
                    tool_calls=[]
                )
            else:
                # User confirmed OR provided all details - FORCE execution
                logger.info(
                    f"Intent confirmed - forcing tool execution",
                    extra={"user_id": user_id, "operation": detected_intent.operation}
                )

            # Handle UPDATE intent (with full params or after confirmation)
            # Also handle update_ask follow-up where user provides details
            if (detected_intent.operation == "update" or detected_intent.operation == "update_ask") and detected_intent.params and not detected_intent.needs_confirmation:
                # User provided update details - FORCE execution
                task_id = detected_intent.task_id

                # If task_title provided (even partial), use find_task with fuzzy matching
                if not task_id and detected_intent.task_title:
                    try:
                        find_params = FindTaskParams(
                            user_id=user_id,
                            title=detected_intent.task_title
                        )
                        find_result = find_task(db, find_params)
                        if find_result:
                            # Check confidence - if low, ask for confirmation
                            if find_result.confidence_score < 80:
                                confirmation_msg = (
                                    f"🔍 I found a task that might match '{detected_intent.task_title}':\n"
                                    f"   '{find_result.title}' (Task #{find_result.task_id}) - {find_result.confidence_score}% match\n\n"
                                    f"Is this the task you want to update?\n"
                                    f"Reply 'yes' to confirm or 'no' to cancel."
                                )
                                
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="user",
                                    content=request.message
                                )
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="assistant",
                                    content=confirmation_msg
                                )
                                conversation_service.update_conversation_timestamp(conversation_id)
                                
                                return ChatResponse(
                                    conversation_id=conversation_id,
                                    response=confirmation_msg,
                                    tool_calls=[]
                                )
                            else:
                                task_id = find_result.task_id
                                logger.info(f"Found task by title (high confidence): '{detected_intent.task_title}' -> task_id={task_id}, confidence={find_result.confidence_score}%")
                        else:
                            # No match - list tasks to help
                            list_params = ListTasksParams(user_id=user_id, status="all")
                            list_result = list_tasks(db, list_params)
                            if list_result.tasks:
                                task_list = "\n".join([f"  • #{t['task_id']}: {t['title']}" for t in list_result.tasks[:10]])
                                error_msg = (
                                    f"I couldn't find a task matching '{detected_intent.task_title}'.\n\n"
                                    f"Here are your current tasks:\n{task_list}\n\n"
                                    f"Please specify the task by ID or exact title."
                                )
                                
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="user",
                                    content=request.message
                                )
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="assistant",
                                    content=error_msg
                                )
                                conversation_service.update_conversation_timestamp(conversation_id)
                                
                                return ChatResponse(
                                    conversation_id=conversation_id,
                                    response=error_msg,
                                    tool_calls=[]
                                )
                    except Exception as e:
                        logger.error(f"Failed to find task: {e}")

                # If still no task_id, try to get from conversation context
                if not task_id:
                    # Check recent conversation for task mentions - look for task title or ID
                    for msg in reversed(conversation_history[-10:]):
                        if msg.get('role') == 'user':
                            user_msg = msg.get('content', '').lower()
                            # Pattern 1: "update the task: [title]" or "i want to update the task: [title]"
                            task_match = re.search(r'(?:update|want\s+to\s+update)\s+(?:the\s+)?task:?\s+(.+?)(?:\s+update|\s+title|\s+priority|\s+deadline|$)', user_msg)
                            if task_match:
                                task_title_from_context = task_match.group(1).strip()
                                # Remove "the" if present at start
                                task_title_from_context = re.sub(r'^(the|a|an)\s+', '', task_title_from_context, flags=re.IGNORECASE)
                                if task_title_from_context and len(task_title_from_context) > 2 and task_title_from_context.lower() != 'the':
                                    try:
                                        find_params = FindTaskParams(
                                            user_id=user_id,
                                            title=task_title_from_context
                                        )
                                        find_result = find_task(db, find_params)
                                        if find_result:
                                            task_id = find_result.task_id
                                            logger.info(f"Found task from context: '{task_title_from_context}' -> task_id={task_id}")
                                            break
                                    except Exception as e:
                                        logger.error(f"Failed to find task from context: {e}")
                        
                        # Also check assistant messages for task mentions
                        if msg.get('role') == 'assistant':
                            assistant_msg = msg.get('content', '').lower()
                            # Pattern: "task '[title]'" or "task \"title\""
                            task_match = re.search(r"task\s+['\"](.+?)['\"]", assistant_msg)
                            if task_match:
                                task_title_from_context = task_match.group(1).strip()
                                if task_title_from_context and len(task_title_from_context) > 2:
                                    try:
                                        find_params = FindTaskParams(
                                            user_id=user_id,
                                            title=task_title_from_context
                                        )
                                        find_result = find_task(db, find_params)
                                        if find_result:
                                            task_id = find_result.task_id
                                            logger.info(f"Found task from assistant context: '{task_title_from_context}' -> task_id={task_id}")
                                            break
                                    except Exception as e:
                                        logger.error(f"Failed to find task from assistant context: {e}")

                if task_id:
                    # Build update params - only include fields that were actually provided
                    update_params = {'task_id': task_id}

                    # Add title if provided
                    if 'title' in detected_intent.params and detected_intent.params['title'] is not None:
                        update_params['title'] = detected_intent.params['title']

                    # Add description if provided
                    if 'description' in detected_intent.params and detected_intent.params['description'] is not None:
                        update_params['description'] = detected_intent.params['description']

                    # Add priority if provided
                    if 'priority' in detected_intent.params and detected_intent.params['priority'] is not None:
                        update_params['priority'] = detected_intent.params['priority']

                    # Handle due_date - parse if provided
                    if 'due_date' in detected_intent.params:
                        due_date_str = detected_intent.params['due_date']
                        if due_date_str is None:
                            # Explicitly remove deadline
                            update_params['due_date'] = None
                        else:
                            # Parse natural language date
                            due_date = parse_natural_date(due_date_str)
                            if due_date:
                                update_params['due_date'] = due_date.isoformat()

                    # Add completed status if provided
                    if 'completed' in detected_intent.params and detected_intent.params['completed'] is not None:
                        update_params['completed'] = detected_intent.params['completed']

                    # Check if we have actual update fields (not just task_id)
                    has_updates = len(update_params) > 1
                    
                    if has_updates:
                        # Check if user already confirmed (needs_confirmation=False means they said "yes")
                        # If already confirmed, execute update directly. Otherwise, show confirmation template.
                        if not detected_intent.needs_confirmation:
                            # User already confirmed - EXECUTE UPDATE DIRECTLY
                            forced_tool_calls.append({
                                'tool': 'update_task',
                                'params': update_params
                            })
                            
                            logger.info(
                                f"FORCED UPDATE (confirmed): task_id={task_id}, update_params={update_params}",
                                extra={
                                    "user_id": user_id, 
                                    "task_id": task_id,
                                    "update_params": update_params
                                }
                            )
                            # Continue to AI agent for response generation
                        else:
                            # User hasn't confirmed yet - show confirmation template
                            # Build confirmation message with formatted template
                            confirmation_lines = ["📝 **Update Task Confirmation**\n"]
                            confirmation_lines.append(f"Task ID: #{task_id}\n")
                            confirmation_lines.append("**Changes to be made:**\n")
                            
                            if 'title' in update_params:
                                confirmation_lines.append(f"  • Title: → \"{update_params['title']}\"")
                            if 'priority' in update_params:
                                confirmation_lines.append(f"  • Priority: → {update_params['priority']}")
                            if 'description' in update_params:
                                desc = update_params['description']
                                if desc:
                                    confirmation_lines.append(f"  • Description: → \"{desc[:50]}{'...' if len(desc) > 50 else ''}\"")
                                else:
                                    confirmation_lines.append(f"  • Description: → (removed)")
                            if 'due_date' in update_params:
                                if update_params['due_date']:
                                    try:
                                        due_dt = datetime.fromisoformat(update_params['due_date'].replace('Z', '+00:00'))
                                        confirmation_lines.append(f"  • Due Date: → {due_dt.strftime('%B %d, %Y at %I:%M %p')}")
                                    except:
                                        confirmation_lines.append(f"  • Due Date: → {update_params['due_date']}")
                                else:
                                    confirmation_lines.append(f"  • Due Date: → (removed)")
                            if 'completed' in update_params:
                                status = "Complete ✅" if update_params['completed'] else "Incomplete ⏳"
                                confirmation_lines.append(f"  • Status: → {status}")
                            
                            confirmation_lines.append("\n**Kya aap sure hain? (Are you sure?)**")
                            confirmation_lines.append("Reply 'yes' to confirm or 'no' to cancel.")
                            
                            confirmation_msg = "\n".join(confirmation_lines)
                            
                            # Store user message and confirmation
                            conversation_service.add_message(
                                conversation_id=conversation_id,
                                user_id=user_id,
                                role="user",
                                content=request.message
                            )
                            conversation_service.add_message(
                                conversation_id=conversation_id,
                                user_id=user_id,
                                role="assistant",
                                content=confirmation_msg
                            )
                            conversation_service.update_conversation_timestamp(conversation_id)
                            
                            logger.info(
                                f"Update confirmation requested: task_id={task_id}, update_params={update_params}",
                                extra={
                                    "user_id": user_id, 
                                    "task_id": task_id,
                                    "update_params": update_params
                                }
                            )
                            
                            return ChatResponse(
                                conversation_id=conversation_id,
                                response=confirmation_msg,
                                tool_calls=[]
                            )
                    else:
                        # No update params provided - this shouldn't happen
                        logger.warning(
                            f"Update intent detected but no update params provided! task_id={task_id}",
                            extra={"user_id": user_id, "detected_intent": str(detected_intent)}
                        )

            # Handle DELETE intent (after confirmation)
            elif detected_intent.operation == "delete" and not detected_intent.needs_confirmation:
                task_id = detected_intent.task_id

                # If task_title provided (even partial), use find_task with fuzzy matching
                if not task_id and detected_intent.task_title:
                    try:
                        find_params = FindTaskParams(
                            user_id=user_id,
                            title=detected_intent.task_title
                        )
                        find_result = find_task(db, find_params)
                        if find_result:
                            # Check confidence - if low, ask for confirmation
                            if find_result.confidence_score < 80:
                                # Low confidence match - ask for confirmation
                                confirmation_msg = (
                                    f"🔍 I found a task that might match '{detected_intent.task_title}':\n"
                                    f"   '{find_result.title}' (Task #{find_result.task_id}) - {find_result.confidence_score}% match\n\n"
                                    f"Is this the task you want to delete?\n"
                                    f"Reply 'yes' to confirm or 'no' to cancel."
                                )
                                
                                # Store pending confirmation
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="user",
                                    content=request.message
                                )
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="assistant",
                                    content=confirmation_msg
                                )
                                conversation_service.update_conversation_timestamp(conversation_id)
                                
                                return ChatResponse(
                                    conversation_id=conversation_id,
                                    response=confirmation_msg,
                                    tool_calls=[]
                                )
                            else:
                                # High confidence - proceed
                                task_id = find_result.task_id
                                logger.info(f"Found task by title (high confidence): '{detected_intent.task_title}' -> task_id={task_id}, confidence={find_result.confidence_score}%")
                        else:
                            # No match found - list tasks to help user
                            list_params = ListTasksParams(user_id=user_id, status="all")
                            list_result = list_tasks(db, list_params)
                            if list_result.tasks:
                                task_list = "\n".join([f"  • #{t['task_id']}: {t['title']}" for t in list_result.tasks[:10]])
                                error_msg = (
                                    f"I couldn't find a task matching '{detected_intent.task_title}'.\n\n"
                                    f"Here are your current tasks:\n{task_list}\n\n"
                                    f"Please specify the task by ID or exact title."
                                )
                                
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="user",
                                    content=request.message
                                )
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="assistant",
                                    content=error_msg
                                )
                                conversation_service.update_conversation_timestamp(conversation_id)
                                
                                return ChatResponse(
                                    conversation_id=conversation_id,
                                    response=error_msg,
                                    tool_calls=[]
                                )
                    except Exception as e:
                        logger.error(f"Failed to find task: {e}")

                if task_id:
                    # FORCE delete_task execution
                    forced_tool_calls.append({
                        'tool': 'delete_task',
                        'params': {'task_id': task_id}
                    })

                    logger.info(
                        f"FORCED DELETE: task_id={task_id}",
                        extra={"user_id": user_id, "task_id": task_id}
                    )

            # Handle COMPLETE intent (after confirmation)
            elif detected_intent.operation == "complete" and not detected_intent.needs_confirmation:
                task_id = detected_intent.task_id

                # If task_title provided (even partial), use find_task with fuzzy matching
                if not task_id and detected_intent.task_title:
                    try:
                        find_params = FindTaskParams(
                            user_id=user_id,
                            title=detected_intent.task_title
                        )
                        find_result = find_task(db, find_params)
                        if find_result:
                            # Check confidence - if low, ask for confirmation
                            if find_result.confidence_score < 80:
                                confirmation_msg = (
                                    f"🔍 I found a task that might match '{detected_intent.task_title}':\n"
                                    f"   '{find_result.title}' (Task #{find_result.task_id}) - {find_result.confidence_score}% match\n\n"
                                    f"Is this the task you want to mark as complete?\n"
                                    f"Reply 'yes' to confirm or 'no' to cancel."
                                )
                                
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="user",
                                    content=request.message
                                )
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="assistant",
                                    content=confirmation_msg
                                )
                                conversation_service.update_conversation_timestamp(conversation_id)
                                
                                return ChatResponse(
                                    conversation_id=conversation_id,
                                    response=confirmation_msg,
                                    tool_calls=[]
                                )
                            else:
                                task_id = find_result.task_id
                                logger.info(f"Found task by title (high confidence): '{detected_intent.task_title}' -> task_id={task_id}, confidence={find_result.confidence_score}%")
                        else:
                            # No match - list tasks
                            list_params = ListTasksParams(user_id=user_id, status="all")
                            list_result = list_tasks(db, list_params)
                            if list_result.tasks:
                                task_list = "\n".join([f"  • #{t['task_id']}: {t['title']}" for t in list_result.tasks[:10]])
                                error_msg = (
                                    f"I couldn't find a task matching '{detected_intent.task_title}'.\n\n"
                                    f"Here are your current tasks:\n{task_list}\n\n"
                                    f"Please specify the task by ID or exact title."
                                )
                                
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="user",
                                    content=request.message
                                )
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="assistant",
                                    content=error_msg
                                )
                                conversation_service.update_conversation_timestamp(conversation_id)
                                
                                return ChatResponse(
                                    conversation_id=conversation_id,
                                    response=error_msg,
                                    tool_calls=[]
                                )
                    except Exception as e:
                        logger.error(f"Failed to find task: {e}")

                if task_id:
                    # FORCE complete_task execution
                    forced_tool_calls.append({
                        'tool': 'complete_task',
                        'params': {'task_id': task_id}
                    })

                    logger.info(
                        f"FORCED COMPLETE: task_id={task_id}",
                        extra={"user_id": user_id, "task_id": task_id}
                    )

            # Handle LIST intent (show tasks)
            elif detected_intent.operation == "list":
                # FORCE list_tasks execution (user_id from auth in execution loop)
                forced_tool_calls.append({
                    'tool': 'list_tasks',
                    'params': {
                        'status': detected_intent.params.get('status', 'all')
                    }
                })

                logger.info(
                    f"FORCED LIST: status={detected_intent.params.get('status', 'all')}",
                    extra={"user_id": user_id, "status": detected_intent.params.get('status', 'all')}
                )

            # Handle ADD intent (create task) - Initialize multi-turn workflow
            elif detected_intent.operation == "add":
                try:
                    title = None
                    if detected_intent.params:
                        title = detected_intent.params.get("title")

                    # Never use command phrases as task title (e.g. "add task" or "delete task" as reply to "what's the title?")
                    COMMAND_PHRASES_AS_TITLE = frozenset([
                        'add task', 'create task', 'new task',
                        'add a task', 'create a task', 'new a task',
                        'add new task', 'create new task',
                        'delete task', 'delete the task', 'remove task', 'remove the task',
                        'update task', 'update the task',
                        'show all tasks', 'show task list', 'list tasks', 'list my tasks',
                        'mark complete', 'mark as complete'
                    ])
                    if title and (title.strip().lower() in COMMAND_PHRASES_AS_TITLE):
                        title = None

                    if title:
                        # User provided title - initialize ADDING_TASK workflow
                        # Extract any optional fields provided upfront
                        initial_priority = detected_intent.params.get("priority") if detected_intent.params else None
                        initial_due_date = detected_intent.params.get("due_date") if detected_intent.params else None
                        initial_description = detected_intent.params.get("description") if detected_intent.params else None

                        # Initialize ADD_TASK state
                        state_data = context_manager.initialize_add_task_state(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            initial_title=title,
                            initial_priority=initial_priority,
                            initial_due_date=initial_due_date,
                            initial_description=initial_description
                        )

                        # Generate prompt based on starting step
                        current_step = state_data.get("step", "confirm")

                        if current_step == "create":
                            # All info provided, create task immediately
                            # T029: Validate title is present
                            if not title or not title.strip():
                                error_msg = "❌ Cannot create task: title is required"
                                logger.error(
                                    "All-at-once task creation failed - missing title",
                                    extra={"user_id": user_id, "title": title}
                                )

                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="user",
                                    content=request.message
                                )
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="assistant",
                                    content=error_msg
                                )
                                conversation_service.update_conversation_timestamp(conversation_id)

                                return ChatResponse(
                                    conversation_id=conversation_id,
                                    response=error_msg,
                                    tool_calls=[]
                                )

                            add_params = {"title": title.strip()}
                            if initial_priority:
                                add_params["priority"] = initial_priority
                            if initial_due_date:
                                add_params["due_date"] = initial_due_date
                            if initial_description:
                                add_params["description"] = initial_description

                            params = AddTaskParams(user_id=user_id, **add_params)
                            result = add_task(db, params)

                            # Reset state
                            context_manager.reset_state_after_completion(conversation_id, user_id)

                            success_msg = f"✅ Task created successfully! Task #{result.task_id}: {result.title}"
                            if result.priority:
                                success_msg += f" ({result.priority} priority)"
                            if result.due_date:
                                success_msg += f", due {result.due_date.strftime('%B %d, %Y')}"

                            conversation_service.add_message(
                                conversation_id=conversation_id,
                                user_id=user_id,
                                role="user",
                                content=request.message
                            )
                            conversation_service.add_message(
                                conversation_id=conversation_id,
                                user_id=user_id,
                                role="assistant",
                                content=success_msg
                            )
                            conversation_service.update_conversation_timestamp(conversation_id)

                            logger.info(
                                f"Task created (all-at-once): task_id={result.task_id}",
                                extra={"user_id": user_id, "task_id": result.task_id}
                            )

                            return ChatResponse(
                                conversation_id=conversation_id,
                                response=success_msg,
                                tool_calls=[{
                                    'tool': 'add_task',
                                    'params': add_params,
                                    'result': {
                                        'task_id': result.task_id,
                                        'title': result.title,
                                        'description': result.description,
                                        'priority': result.priority,
                                        'due_date': result.due_date.isoformat() if result.due_date else None,
                                        'completed': result.completed,
                                        'created_at': result.created_at.isoformat()
                                    }
                                }]
                            )
                        elif current_step == "confirm":
                            prompt_msg = f"Would you like to add the task: '{title}'? Reply 'yes' to continue or 'no' to cancel."
                        elif current_step == "priority":
                            prompt_msg = "What priority should this task have? (high, medium, or low)"
                        elif current_step == "deadline":
                            prompt_msg = "Would you like to set a deadline for this task? (e.g., 'tomorrow', 'next Friday', 'Jan 20', or 'no' to skip)"
                        elif current_step == "description":
                            prompt_msg = "Would you like to add a description for this task? (Enter the description or 'no' to skip)"
                        else:
                            prompt_msg = "Let's add this task step by step."

                        # Store messages
                        conversation_service.add_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            role="user",
                            content=request.message
                        )
                        conversation_service.add_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            role="assistant",
                            content=prompt_msg
                        )
                        conversation_service.update_conversation_timestamp(conversation_id)

                        logger.info(
                            f"ADDING_TASK workflow initialized: step={current_step}",
                            extra={"user_id": user_id, "title": title, "step": current_step}
                        )

                        return ChatResponse(
                            conversation_id=conversation_id,
                            response=prompt_msg,
                            tool_calls=[]
                        )
                    else:
                        # User wants to add a task but didn't provide title
                        # Ask for the task title
                        add_msg = (
                            "Sure! I'd be happy to help you add a task. "
                            "What's the title of the task you'd like to add?"
                        )

                        conversation_service.add_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            role="user",
                            content=request.message
                        )
                        conversation_service.add_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            role="assistant",
                            content=add_msg
                        )
                        conversation_service.update_conversation_timestamp(conversation_id)

                        logger.info(
                            f"ADD intent detected - asking for task title",
                            extra={"user_id": user_id, "user_message": request.message}
                        )

                        return ChatResponse(
                            conversation_id=conversation_id,
                            response=add_msg,
                            tool_calls=[]
                        )
                except Exception as e:
                    logger.error(
                        f"Error handling ADD intent: {e}",
                        exc_info=True,
                        extra={"user_id": user_id, "user_message": request.message}
                    )
                    raise  # Re-raise to be caught by outer exception handler

            # Handle INCOMPLETE intent (mark as not done/pending)
            elif detected_intent.operation == "incomplete" and not detected_intent.needs_confirmation:
                task_id = detected_intent.task_id

                # If task_title provided (even partial), use find_task with fuzzy matching
                if not task_id and detected_intent.task_title:
                    try:
                        find_params = FindTaskParams(
                            user_id=user_id,
                            title=detected_intent.task_title
                        )
                        find_result = find_task(db, find_params)
                        if find_result:
                            # Check confidence - if low, ask for confirmation
                            if find_result.confidence_score < 80:
                                confirmation_msg = (
                                    f"🔍 I found a task that might match '{detected_intent.task_title}':\n"
                                    f"   '{find_result.title}' (Task #{find_result.task_id}) - {find_result.confidence_score}% match\n\n"
                                    f"Is this the task you want to mark as incomplete?\n"
                                    f"Reply 'yes' to confirm or 'no' to cancel."
                                )
                                
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="user",
                                    content=request.message
                                )
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="assistant",
                                    content=confirmation_msg
                                )
                                conversation_service.update_conversation_timestamp(conversation_id)
                                
                                return ChatResponse(
                                    conversation_id=conversation_id,
                                    response=confirmation_msg,
                                    tool_calls=[]
                                )
                            else:
                                task_id = find_result.task_id
                                logger.info(f"Found task by title (high confidence): '{detected_intent.task_title}' -> task_id={task_id}, confidence={find_result.confidence_score}%")
                        else:
                            # No match - list tasks
                            list_params = ListTasksParams(user_id=user_id, status="all")
                            list_result = list_tasks(db, list_params)
                            if list_result.tasks:
                                task_list = "\n".join([f"  • #{t['task_id']}: {t['title']}" for t in list_result.tasks[:10]])
                                error_msg = (
                                    f"I couldn't find a task matching '{detected_intent.task_title}'.\n\n"
                                    f"Here are your current tasks:\n{task_list}\n\n"
                                    f"Please specify the task by ID or exact title."
                                )
                                
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="user",
                                    content=request.message
                                )
                                conversation_service.add_message(
                                    conversation_id=conversation_id,
                                    user_id=user_id,
                                    role="assistant",
                                    content=error_msg
                                )
                                conversation_service.update_conversation_timestamp(conversation_id)
                                
                                return ChatResponse(
                                    conversation_id=conversation_id,
                                    response=error_msg,
                                    tool_calls=[]
                                )
                    except Exception as e:
                        logger.error(f"Failed to find task: {e}")

                if task_id:
                    # FORCE update_task execution with completed=False
                    forced_tool_calls.append({
                        'tool': 'update_task',
                        'params': {
                            'task_id': task_id,
                            'completed': False
                        }
                    })

                    logger.info(
                        f"FORCED INCOMPLETE: task_id={task_id}",
                        extra={"user_id": user_id, "task_id": task_id}
                    )

        # Initialize agent tools (T064)
        tools = register_tools()

        # Run AI agent (T065)
        # If forced tool calls exist, we still call AI for conversational response
        # BUT: If we have confirmed forced tool calls, skip AI agent to avoid errors
        skip_ai_agent = False
        if forced_tool_calls:
            # Check if all forced tool calls are confirmed operations (add, update, delete, complete, incomplete, list)
            confirmed_operations = ['add_task', 'update_task', 'delete_task', 'complete_task', 'list_tasks']
            skip_ai_agent = all(
                tool_call.get('tool') in confirmed_operations 
                for tool_call in forced_tool_calls
            )
        
        if skip_ai_agent:
            # Skip AI agent for confirmed operations - generate response directly
            logger.info(
                f"Skipping AI agent for confirmed forced tool calls: {[tc.get('tool') for tc in forced_tool_calls]}",
                extra={"user_id": user_id, "forced_tools": [tc.get('tool') for tc in forced_tool_calls]}
            )
            agent_response = AgentResponse(
                response="",  # Will be generated from tool results
                tool_calls=[]
            )
        else:
            agent_response = await run_agent(
                user_id=user_id,
                message=request.message,
                conversation_history=conversation_history,
                tools=tools
            )

        # Execute tool calls if any
        # PRIORITY: Forced tool calls execute FIRST, then AI-suggested tools
        executed_tools = []
        tool_errors = []
        seen_tool_calls = set()  # Track tool call signatures for deduplication

        # STEP 1: Execute FORCED tool calls (from intent detector)
        all_tool_calls = forced_tool_calls + (agent_response.tool_calls if hasattr(agent_response, 'tool_calls') and agent_response.tool_calls else [])

        if all_tool_calls:
            for tool_call in all_tool_calls:
                tool_name = tool_call.get('tool')
                tool_params = tool_call.get('params', {})

                # Create signature for deduplication (exclude user_id)
                import json
                param_copy = {k: v for k, v in tool_params.items() if k != 'user_id'}
                tool_signature = f"{tool_name}:{json.dumps(param_copy, sort_keys=True)}"

                # Skip if we've already executed this exact tool call
                if tool_signature in seen_tool_calls:
                    logger.warning(
                        f"Skipping duplicate tool call: {tool_signature}",
                        extra={"user_id": user_id, "tool": tool_name}
                    )
                    continue

                seen_tool_calls.add(tool_signature)

                if tool_name == 'add_task':
                    # Execute add_task tool
                    try:
                        logger.info(
                            f"Executing add_task for user {user_id}",
                            extra={
                                "user_id": user_id,
                                "title": tool_params.get('title'),
                                "priority": tool_params.get('priority', 'medium')
                            }
                        )
                        
                        # Validate title is provided
                        if not tool_params.get('title') or not tool_params.get('title').strip():
                            raise ValueError("Task title is required. Please provide a title for the task.")
                        
                        # Pass due_date as string - add_task tool will parse it
                        params = AddTaskParams(
                            user_id=user_id,
                            title=tool_params.get('title').strip(),
                            description=tool_params.get('description'),
                            priority=tool_params.get('priority', 'medium'),
                            due_date=tool_params.get('due_date')  # Pass as string
                        )
                        result = add_task(db, params)
                        
                        logger.info(
                            f"add_task succeeded: task_id={result.task_id}, title={result.title}",
                            extra={
                                "user_id": user_id,
                                "task_id": result.task_id,
                                "task_title": result.title
                            }
                        )
                        
                        executed_tools.append({
                            'tool': 'add_task',
                            'params': tool_params,
                            'result': {
                                'task_id': result.task_id,
                                'title': result.title,
                                'description': result.description,
                                'priority': result.priority,
                                'due_date': result.due_date.isoformat() if result.due_date else None,
                                'completed': result.completed,
                                'created_at': result.created_at.isoformat()
                            }
                        })
                    except ValueError as e:
                        # Validation errors - provide user-friendly message
                        error_msg = str(e)
                        logger.error(
                            f"add_task validation failed: {error_msg}",
                            extra={
                                "user_id": user_id,
                                "error": error_msg,
                                "error_type": "validation_error",
                                "params": tool_params
                            },
                            exc_info=True
                        )
                        tool_errors.append({"tool": "add_task", "error": error_msg})
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(
                            f"add_task execution failed: {error_msg}",
                            extra={
                                "user_id": user_id,
                                "error": error_msg,
                                "error_type": type(e).__name__,
                                "params": tool_params
                            },
                            exc_info=True
                        )
                        tool_errors.append({"tool": "add_task", "error": error_msg})
                        # Continue even if tool fails

                elif tool_name == 'list_tasks':
                    # Execute list_tasks tool
                    try:
                        params = ListTasksParams(
                            user_id=user_id,
                            status=tool_params.get('status', 'all')
                        )
                        result = list_tasks(db, params)
                        executed_tools.append({
                            'tool': 'list_tasks',
                            'params': tool_params,
                            'result': {
                                'tasks': [
                                    {
                                        'task_id': task['task_id'],
                                        'title': task['title'],
                                        'description': task['description'],
                                        'priority': task['priority'],
                                        # list_tasks tool already returns due_date as ISO string (or None)
                                        'due_date': task.get('due_date'),
                                        'completed': task['completed'],
                                        # Handle both datetime and string formats for created_at
                                        'created_at': task['created_at'].isoformat() if hasattr(task['created_at'], 'isoformat') else task['created_at']
                                    }
                                    for task in result.tasks
                                ],
                                'count': result.count
                            }
                        })
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}", exc_info=True)
                        tool_errors.append({"tool": "list_tasks", "error": str(e)})
                        executed_tools.append({
                            'tool': 'list_tasks',
                            'params': tool_params,
                            'result': {'error': str(e)}
                        })
                        # Continue even if tool fails

                elif tool_name == 'complete_task':
                    # Execute complete_task tool
                    try:
                        params = CompleteTaskParams(
                            user_id=user_id,
                            task_id=tool_params.get('task_id')
                        )
                        result = complete_task(db, params)
                        executed_tools.append({
                            'tool': 'complete_task',
                            'params': tool_params,
                            'result': {
                                'task_id': result.task_id,
                                'title': result.title,
                                'description': result.description,
                                'priority': result.priority,
                                'due_date': result.due_date.isoformat() if result.due_date else None,
                                'completed': result.completed,
                                'updated_at': result.updated_at.isoformat()
                            }
                        })
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}", exc_info=True)
                        tool_errors.append({"tool": "complete_task", "error": str(e)})
                        executed_tools.append({
                            'tool': 'complete_task',
                            'params': tool_params,
                            'result': {'error': str(e)}
                        })
                        # Continue even if tool fails

                elif tool_name == 'update_task':
                    # Execute update_task tool
                    try:
                        logger.info(
                            f"Executing update_task for user {user_id}",
                            extra={
                                "user_id": user_id,
                                "task_id": tool_params.get('task_id'),
                                "params": tool_params
                            }
                        )

                        # IMPORTANT: Only pass fields that were actually provided.
                        # Passing title=None/priority=None explicitly can overwrite existing values.
                        update_kwargs = {
                            "user_id": user_id,
                            "task_id": tool_params.get("task_id"),
                        }

                        if "title" in tool_params:
                            update_kwargs["title"] = tool_params.get("title")
                        if "description" in tool_params:
                            update_kwargs["description"] = tool_params.get("description")
                        if "priority" in tool_params:
                            update_kwargs["priority"] = tool_params.get("priority")
                        if "completed" in tool_params:
                            update_kwargs["completed"] = tool_params.get("completed")

                        # due_date can be missing (no change), null (remove), or string (set)
                        # Supports: ISO format, natural language ("tomorrow at 3pm"), and "Z" suffix
                        if "due_date" in tool_params:
                            due_date_str = tool_params.get("due_date")
                            if due_date_str is None:
                                update_kwargs["due_date"] = None
                                logger.info(f"update_task: Removing due_date (set to None)")
                            elif isinstance(due_date_str, str) and due_date_str.strip():
                                # Try parse_natural_date first (handles natural language + ISO)
                                parsed_date = parse_natural_date(due_date_str)
                                if parsed_date:
                                    update_kwargs["due_date"] = parsed_date
                                    logger.info(f"update_task: Parsed due_date '{due_date_str}' → {parsed_date}")
                                else:
                                    # Fallback: Try ISO format with Z suffix handling
                                    try:
                                        # Handle "Z" suffix (UTC timezone indicator)
                                        clean_date_str = due_date_str.replace('Z', '+00:00')
                                        update_kwargs["due_date"] = datetime.fromisoformat(clean_date_str)
                                        logger.info(f"update_task: Parsed ISO due_date '{due_date_str}'")
                                    except (ValueError, TypeError) as e:
                                        logger.error(f"update_task: Failed to parse due_date '{due_date_str}': {e}")
                                        raise ValueError(f"Invalid due_date format: {due_date_str}. Use ISO 8601 format (e.g., '2026-01-15T14:30:00') or natural language (e.g., 'tomorrow at 3pm').")

                        params = UpdateTaskParams(**update_kwargs)
                        result = update_task(db, params)

                        logger.info(
                            f"update_task succeeded: task_id={result.task_id}, title={result.title}",
                            extra={
                                "user_id": user_id,
                                "task_id": result.task_id,
                                "updated_fields": {k: v for k, v in tool_params.items() if v is not None}
                            }
                        )

                        executed_tools.append({
                            'tool': 'update_task',
                            'params': tool_params,
                            'result': {
                                'task_id': result.task_id,
                                'title': result.title,
                                'description': result.description,
                                'priority': result.priority,
                                'due_date': result.due_date.isoformat() if result.due_date else None,
                                'completed': result.completed,
                                'updated_at': result.updated_at.isoformat()
                            }
                        })
                    except Exception as e:
                        logger.error(
                            f"update_task failed for task_id={tool_params.get('task_id')}: {str(e)}",
                            extra={
                                "user_id": user_id,
                                "task_id": tool_params.get('task_id'),
                                "error_type": type(e).__name__,
                                "params": tool_params
                            },
                            exc_info=True
                        )
                        tool_errors.append({"tool": "update_task", "error": str(e)})
                        executed_tools.append({
                            'tool': 'update_task',
                            'params': tool_params,
                            'result': {'error': str(e)}
                        })
                        # Continue even if tool fails

                elif tool_name == 'delete_task':
                    # Execute delete_task tool
                    try:
                        logger.info(
                            f"Executing delete_task for user {user_id}",
                            extra={
                                "user_id": user_id,
                                "task_id": tool_params.get('task_id')
                            }
                        )

                        params = DeleteTaskParams(
                            user_id=user_id,
                            task_id=tool_params.get('task_id')
                        )
                        result = delete_task(db, params)

                        logger.info(
                            f"delete_task succeeded: task_id={result.task_id}, title={result.title}",
                            extra={
                                "user_id": user_id,
                                "task_id": result.task_id,
                                "task_title": result.title
                            }
                        )

                        executed_tools.append({
                            'tool': 'delete_task',
                            'params': tool_params,
                            'result': {
                                'task_id': result.task_id,
                                'title': result.title,
                                'success': result.success
                            }
                        })
                    except Exception as e:
                        logger.error(
                            f"delete_task failed for task_id={tool_params.get('task_id')}: {str(e)}",
                            extra={
                                "user_id": user_id,
                                "task_id": tool_params.get('task_id'),
                                "error_type": type(e).__name__
                            },
                            exc_info=True
                        )
                        tool_errors.append({"tool": "delete_task", "error": str(e)})
                        executed_tools.append({
                            'tool': 'delete_task',
                            'params': tool_params,
                            'result': {'error': str(e)}
                        })
                        # Continue even if tool fails

                elif tool_name == 'set_task_deadline':
                    # Execute set_task_deadline tool
                    try:
                        from ..mcp_tools.set_task_deadline import (
                            set_task_deadline,
                            SetTaskDeadlineParams
                        )

                        logger.info(
                            f"Executing set_task_deadline for user {user_id}",
                            extra={
                                "user_id": user_id,
                                "task_id": tool_params.get('task_id'),
                                "due_date": tool_params.get('due_date')
                            }
                        )

                        # Parse due_date if it's a string (natural language or ISO)
                        due_date_value = tool_params.get('due_date')
                        if due_date_value and isinstance(due_date_value, str):
                            due_date_value = due_date_value.strip()
                            # Try parse_natural_date first (handles natural language + ISO)
                            parsed_date = parse_natural_date(due_date_value)
                            if parsed_date:
                                due_date_value = parsed_date.isoformat()
                                logger.info(f"set_task_deadline: Parsed due_date '{tool_params.get('due_date')}' → {due_date_value}")
                            else:
                                # Fallback: Handle "Z" suffix for ISO dates
                                try:
                                    clean_date_str = due_date_value.replace('Z', '+00:00')
                                    parsed = datetime.fromisoformat(clean_date_str)
                                    due_date_value = parsed.isoformat()
                                    logger.info(f"set_task_deadline: Parsed ISO due_date '{tool_params.get('due_date')}' → {due_date_value}")
                                except (ValueError, TypeError) as e:
                                    logger.error(f"set_task_deadline: Failed to parse date '{due_date_value}': {e}")
                                    raise ValueError(f"Invalid due_date format: {due_date_value}. Use ISO 8601 format or natural language.")

                        params = SetTaskDeadlineParams(
                            user_id=user_id,
                            task_id=tool_params.get('task_id'),
                            due_date=due_date_value
                        )
                        result = set_task_deadline(db, params)

                        logger.info(
                            f"set_task_deadline succeeded: task_id={result.task_id}, action={result.action}",
                            extra={
                                "user_id": user_id,
                                "task_id": result.task_id,
                                "action": result.action,
                                "new_due_date": result.due_date.isoformat() if result.due_date else None
                            }
                        )

                        executed_tools.append({
                            'tool': 'set_task_deadline',
                            'params': tool_params,
                            'result': {
                                'task_id': result.task_id,
                                'title': result.title,
                                'due_date': result.due_date.isoformat() if result.due_date else None,
                                'action': result.action,
                                'updated_at': result.updated_at.isoformat()
                            }
                        })
                    except Exception as e:
                        logger.error(
                            f"set_task_deadline failed for task_id={tool_params.get('task_id')}: {str(e)}",
                            extra={
                                "user_id": user_id,
                                "task_id": tool_params.get('task_id'),
                                "error_type": type(e).__name__
                            },
                            exc_info=True
                        )
                        # Continue even if tool fails

                elif tool_name == 'find_task':
                    # Execute find_task tool
                    try:
                        params = FindTaskParams(
                            user_id=user_id,
                            title=tool_params.get('title')
                        )
                        result = find_task(db, params)

                        # Return find_task result without auto-execution
                        # Agent will ask for confirmation before executing delete/update/complete
                        executed_tools.append({
                            'tool': 'find_task',
                            'params': tool_params,
                            'result': {
                                'found': result is not None,
                                'task': {
                                    'task_id': result.task_id,
                                    'title': result.title,
                                    'description': result.description,
                                    'priority': result.priority,
                                    'completed': result.completed,
                                    # find_task tool returns created_at as a string already
                                    'created_at': (
                                        result.created_at.isoformat()
                                        if hasattr(result.created_at, "isoformat")
                                        else result.created_at
                                    ) if result and result.created_at else None
                                } if result else None
                            }
                        })

                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}", exc_info=True)
                        tool_errors.append({"tool": "find_task", "error": str(e)})
                        executed_tools.append({
                            'tool': 'find_task',
                            'params': tool_params,
                            'result': {'error': str(e)}
                        })
                        # Continue even if tool fails

                elif tool_name == 'set_reminder':
                    # Execute set_reminder tool (Phase V - US4)
                    try:
                        logger.info(
                            f"Executing set_reminder for user {user_id}",
                            extra={
                                "user_id": user_id,
                                "task_id": tool_params.get('task_id'),
                                "remind_before_natural": tool_params.get('remind_before_natural')
                            }
                        )

                        params = SetReminderParams(
                            task_id=tool_params.get('task_id'),
                            remind_before_natural=tool_params.get('remind_before_natural'),
                            user_id=user_id
                        )
                        result = set_reminder(params, db)

                        logger.info(
                            f"set_reminder succeeded: task_id={tool_params.get('task_id')}, "
                            f"intervals={result.intervals}",
                            extra={
                                "user_id": user_id,
                                "task_id": tool_params.get('task_id'),
                                "intervals": result.intervals,
                                "reminder_times": result.reminder_times
                            }
                        )

                        executed_tools.append({
                            'tool': 'set_reminder',
                            'params': tool_params,
                            'result': {
                                'success': result.success,
                                'message': result.message,
                                'intervals': result.intervals,
                                'reminder_times': result.reminder_times,
                                'warning': result.warning
                            }
                        })
                    except Exception as e:
                        logger.error(
                            f"set_reminder failed for task_id={tool_params.get('task_id')}: {str(e)}",
                            extra={
                                "user_id": user_id,
                                "task_id": tool_params.get('task_id'),
                                "error_type": type(e).__name__
                            },
                            exc_info=True
                        )
                        tool_errors.append({"tool": "set_reminder", "error": str(e)})
                        executed_tools.append({
                            'tool': 'set_reminder',
                            'params': tool_params,
                            'result': {'error': str(e)}
                        })
                        # Continue even if tool fails

                elif tool_name == 'update_notification_preferences':
                    # Execute update_notification_preferences tool (Phase V - US5)
                    try:
                        logger.info(
                            f"Executing update_notification_preferences for user {user_id}",
                            extra={
                                "user_id": user_id,
                                "email": tool_params.get('email'),
                                "push": tool_params.get('push'),
                                "in_app": tool_params.get('in_app')
                            }
                        )

                        from ..mcp_tools.update_notification_preferences import (
                            update_notification_preferences,
                            UpdateNotificationPreferencesParams
                        )

                        params = UpdateNotificationPreferencesParams(
                            user_id=user_id,
                            email=tool_params.get('email'),
                            push=tool_params.get('push'),
                            in_app=tool_params.get('in_app')
                        )
                        result = update_notification_preferences(params, db)

                        logger.info(
                            f"update_notification_preferences succeeded: "
                            f"email={result.email}, push={result.push}, in_app={result.in_app}",
                            extra={
                                "user_id": user_id,
                                "email": result.email,
                                "push": result.push,
                                "in_app": result.in_app
                            }
                        )

                        executed_tools.append({
                            'tool': 'update_notification_preferences',
                            'params': tool_params,
                            'result': {
                                'success': result.success,
                                'message': result.message,
                                'email': result.email,
                                'push': result.push,
                                'in_app': result.in_app
                            }
                        })
                    except Exception as e:
                        logger.error(
                            f"update_notification_preferences failed: {str(e)}",
                            extra={
                                "user_id": user_id,
                                "error_type": type(e).__name__
                            },
                            exc_info=True
                        )
                        tool_errors.append({"tool": "update_notification_preferences", "error": str(e)})
                        executed_tools.append({
                            'tool': 'update_notification_preferences',
                            'params': tool_params,
                            'result': {'error': str(e)}
                        })
                        # Continue even if tool fails

        # Store user message in database (T066)
        conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=request.message
        )

        # Return response (T068)
        # Enhance response for list_tasks tool with actual task data
        final_response = agent_response.response
        
        # If we skipped AI agent, generate response from tool results
        if skip_ai_agent and executed_tools:
            response_lines = []
            for tool_call in executed_tools:
                tool_name = tool_call.get('tool')
                tool_result = tool_call.get('result', {})
                
                if tool_name == 'add_task' and 'error' not in tool_result:
                    task_id = tool_result.get('task_id')
                    title = tool_result.get('title', 'task')
                    response_lines.append(f"✅ I've added task #{task_id}: '{title}' to your tasks.")
                elif tool_name == 'update_task' and 'error' not in tool_result:
                    task_id = tool_result.get('task_id')
                    title = tool_result.get('title', 'task')
                    updates = []
                    if 'priority' in tool_call.get('params', {}):
                        updates.append(f"priority to {tool_result.get('priority')}")
                    if 'due_date' in tool_call.get('params', {}):
                        if tool_result.get('due_date'):
                            updates.append("due date")
                        else:
                            updates.append("removed due date")
                    if 'completed' in tool_call.get('params', {}):
                        status = "complete" if tool_result.get('completed') else "incomplete"
                        updates.append(f"marked as {status}")
                    if 'title' in tool_call.get('params', {}):
                        updates.append(f"title to '{tool_result.get('title')}'")
                    
                    if updates:
                        response_lines.append(f"✅ I've updated task #{task_id} ({title}): {', '.join(updates)}.")
                    else:
                        response_lines.append(f"✅ I've updated task #{task_id} ({title}).")
                elif tool_name == 'delete_task' and 'error' not in tool_result:
                    task_id = tool_result.get('task_id')
                    title = tool_result.get('title', 'task')
                    response_lines.append(f"✅ I've removed task #{task_id} ({title}) from your tasks.")
                elif tool_name == 'complete_task' and 'error' not in tool_result:
                    task_id = tool_result.get('task_id')
                    title = tool_result.get('title', 'task')
                    response_lines.append(f"✅ I've marked task #{task_id} ({title}) as complete.")
            
            if response_lines:
                final_response = "\n".join(response_lines)
            elif not final_response:
                final_response = "✅ Done!"
        
        if tool_errors:
            # Never claim success if a tool failed
            lines = ["⚠️ I couldn't complete your request due to an error:"]
            for err in tool_errors[:3]:
                lines.append(f"- {err.get('tool')}: {err.get('error')}")
            if len(tool_errors) > 3:
                lines.append(f"- ...and {len(tool_errors) - 3} more")
            final_response = "\n".join(lines)

        if executed_tools:
            for tool_call in executed_tools:
                if tool_call.get('tool') == 'list_tasks' and tool_call.get('result'):
                    result = tool_call['result']
                    tasks = result.get('tasks', [])
                    count = result.get('count', 0)

                    if count == 0:
                        final_response = "📋 You don't have any tasks yet. Add your first task above!"
                    else:
                        # Use proper formatting function with all details
                        from ..ai_agent.utils import format_task_list_response
                        # Ensure tasks have due_date field
                        formatted_tasks = []
                        for task in tasks:
                            task_dict = {
                                'task_id': task.get('task_id'),
                                'title': task.get('title'),
                                'completed': task.get('completed', False),
                                'priority': task.get('priority', 'medium'),
                                'due_date': task.get('due_date')  # Include due_date if present
                            }
                            formatted_tasks.append(task_dict)
                        
                        final_response = format_task_list_response(formatted_tasks)

        # Store assistant response in database (T066) with tool_calls
        # IMPORTANT: store the computed final_response (frontend reloads from DB)
        conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=final_response,
            tool_calls=executed_tools if executed_tools else None
        )

        # Update conversation timestamp (T067)
        conversation_service.update_conversation_timestamp(conversation_id)

        return ChatResponse(
            conversation_id=conversation_id,
            response=final_response,
            tool_calls=executed_tools
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Internal errors (T069)
        logger.error(
            f"Chat endpoint failed for user {user_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )
