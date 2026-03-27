"""AI Agent Execution Runner.

This module handles the execution of the AI agent with conversation history
and user messages, orchestrating tool calls and response generation.

Enhanced with:
- Natural language date parsing
- Batch operation detection
- Smart priority suggestions
- Fuzzy task lookup
"""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from openai import OpenAI, APIError, AuthenticationError, RateLimitError, APIConnectionError

from .agent import initialize_agent, get_system_prompt
from .tools import register_tools
from ..mcp_tools.find_task import find_task, FindTaskParams
from ..utils.performance import log_execution_time, track_performance
from .utils import (
    parse_natural_date,
    detect_batch_operation,
    suggest_priority_from_keywords,
    validate_task_data
)

logger = logging.getLogger(__name__)


def enhance_tool_parameters(
    tool_name: str,
    params: Dict[str, Any],
    user_message: str
) -> Dict[str, Any]:
    """Enhance tool parameters with intelligent preprocessing.

    Features:
    - Parse natural language dates to ISO format
    - Auto-suggest priority from keywords
    - Validate task data

    Args:
        tool_name: Name of the tool being called
        params: Original tool parameters
        user_message: Original user message for context

    Returns:
        Enhanced parameters dictionary
    """
    enhanced_params = params.copy()

    # Natural Language Date Parsing for add_task, update_task, set_task_deadline, and set_recurring
    if tool_name in ['add_task', 'update_task', 'set_task_deadline', 'set_recurring']:
        # Parse due_date if present as string
        if 'due_date' in params and isinstance(params['due_date'], str):
            date_str = params['due_date']
            parsed_date = parse_natural_date(date_str)

            if parsed_date:
                enhanced_params['due_date'] = parsed_date.isoformat()
                logger.info(
                    f"Parsed natural date '{date_str}' → {enhanced_params['due_date']}"
                )
            else:
                logger.warning(f"Failed to parse date: '{date_str}'")
                # Keep original value, let tool validation handle it

        # Parse end_date for set_recurring (Phase V)
        if tool_name == 'set_recurring' and 'end_date' in params and isinstance(params['end_date'], str):
            end_date_str = params['end_date']
            parsed_end_date = parse_natural_date(end_date_str)

            if parsed_end_date:
                enhanced_params['end_date'] = parsed_end_date.isoformat()
                logger.info(
                    f"Parsed recurrence end date '{end_date_str}' → {enhanced_params['end_date']}"
                )
            else:
                logger.warning(f"Failed to parse recurrence end date: '{end_date_str}'")
                # Keep original value, let tool validation handle it

        # Auto-suggest priority for add_task if not provided
        if tool_name == 'add_task' and 'priority' not in params:
            title = params.get('title', '')
            description = params.get('description', '')
            suggested_priority = suggest_priority_from_keywords(title, description)

            if suggested_priority != 'medium':
                enhanced_params['priority'] = suggested_priority
                logger.info(
                    f"Auto-suggested priority '{suggested_priority}' from keywords"
                )

        # Validate task data
        title = params.get('title') if tool_name == 'add_task' else None
        due_date_obj = None
        if 'due_date' in enhanced_params and isinstance(enhanced_params['due_date'], str):
            try:
                due_date_obj = datetime.fromisoformat(enhanced_params['due_date'])
            except:
                pass

        is_valid, error_msg = validate_task_data(title=title, due_date=due_date_obj)
        if not is_valid:
            logger.warning(f"Task validation failed: {error_msg}")
            # Return params with validation warning
            enhanced_params['_validation_warning'] = error_msg

    return enhanced_params


def detect_batch_request(message: str) -> Optional[Dict[str, Any]]:
    """Detect if user message requests a batch operation.

    Args:
        message: User message

    Returns:
        Batch operation dict or None

    Examples:
        "delete all completed tasks" → {"operation": "delete", "filter": "completed"}
        "mark all high priority as done" → {"operation": "complete", "filter": "high"}
    """
    batch_op = detect_batch_operation(message)

    if batch_op:
        logger.info(
            f"Detected batch operation: {batch_op['operation']} "
            f"for filter: {batch_op.get('filter', 'all')}"
        )

    return batch_op


class AgentResponse:
    """Response from AI agent execution."""

    def __init__(
        self,
        response: str,
        tool_calls: List[Dict[str, Any]] = None
    ):
        """Initialize agent response.

        Args:
            response: Natural language response from agent
            tool_calls: List of tool calls made by agent
        """
        self.response = response
        self.tool_calls = tool_calls or []


@log_execution_time("run_ai_agent")
async def run_agent(
    user_id: str,
    message: str,
    conversation_history: List[Dict[str, str]],
    tools: List[Dict[str, Any]] = None
) -> AgentResponse:
    """Run AI agent with user message and conversation history.

    Args:
        user_id: ID of the authenticated user
        message: User's message
        conversation_history: List of previous messages with role and content
        tools: Optional list of tool definitions (defaults to registered tools)

    Returns:
        AgentResponse with natural language response and tool calls

    Error Handling:
        - OpenAI API timeout → Returns friendly error message
        - Tool execution failure → Logs error, returns graceful message
        - Invalid response → Falls back to clarification prompt

    Example:
        >>> history = [
        ...     {"role": "user", "content": "Add task to buy milk"},
        ...     {"role": "assistant", "content": "I've added 'Buy milk'"}
        ... ]
        >>> response = await run_agent(
        ...     user_id="user-123",
        ...     message="Show my tasks",
        ...     conversation_history=history
        ... )
        >>> assert response.response is not None
    """
    try:
        # Initialize agent with tools
        with track_performance("agent_initialization", user_id):
            if tools is None:
                tools = register_tools()

            client = initialize_agent(tools)

        # Detect batch operations before sending to agent
        batch_operation = detect_batch_request(message)
        if batch_operation:
            logger.info(
                f"Batch operation detected for user {user_id}: "
                f"{batch_operation['operation']} with filter {batch_operation.get('filter')}"
            )
            # Add context to system prompt for batch handling
            # Agent will use list_tasks + multiple delete/complete calls

        # Build messages array with system prompt + history + new message
        with track_performance("agent_message_preparation", user_id):
            messages = [{"role": "system", "content": get_system_prompt()}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": message})
            # Conversation history stores app-level tool metadata, not OpenAI tool_calls format.
            # Strip it before sending to Chat Completions to avoid 400 errors.
            for msg in messages:
                if isinstance(msg, dict):
                    msg.pop("tool_calls", None)

        # Call OpenAI API with tools
        with track_performance("agent_execution", user_id):
            logger.info(
                f"Agent execution for user {user_id}: message length {len(message)}"
            )

            # Call OpenAI chat completions with function calling
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto"  # Let the model decide when to use tools
            )

            # Extract response
            response_message = completion.choices[0].message
            response_text = response_message.content or ""

            # Extract tool calls if any
            tool_calls_data = []
            if response_message.tool_calls:
                import json
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    raw_params = json.loads(tool_call.function.arguments)

                    # Enhance parameters with intelligent preprocessing
                    enhanced_params = enhance_tool_parameters(
                        tool_name=tool_name,
                        params=raw_params,
                        user_message=message
                    )

                    # Check for validation warnings
                    if '_validation_warning' in enhanced_params:
                        logger.warning(
                            f"Tool parameter validation warning: "
                            f"{enhanced_params.pop('_validation_warning')}"
                        )

                    # CRITICAL: Inject user_id into tool params (AI doesn't know user_id)
                    enhanced_params['user_id'] = user_id
                    
                    tool_calls_data.append({
                        "tool": tool_name,
                        "params": enhanced_params
                    })

                    logger.info(
                        f"Enhanced tool call: {tool_name} with params: "
                        f"{list(enhanced_params.keys())}"
                    )

            # CRITICAL FIX: Generate response if empty but tools were called
            if not response_text.strip() and tool_calls_data:
                # Generate generic confirmation based on tool type
                tool_name = tool_calls_data[0]['tool']
                tool_params = tool_calls_data[0]['params']

                if tool_name == 'add_task':
                    title = tool_params.get('title', 'task')
                    priority = tool_params.get('priority', 'medium')
                    response_text = f"I've added '{title}' to your tasks with {priority} priority."
                elif tool_name == 'list_tasks':
                    response_text = "Here are your tasks:"
                elif tool_name == 'complete_task':
                    task_id = tool_params.get('task_id', '')
                    # Phase V: Check if next occurrence was created
                    next_occurrence = tool_params.get('next_occurrence')
                    if next_occurrence:
                        next_due = next_occurrence.get('due_date', '')
                        response_text = f"I've marked task {task_id} as complete. The next occurrence has been created for {next_due}."
                    else:
                        response_text = f"I've marked task {task_id} as complete."
                elif tool_name == 'update_task':
                    task_id = tool_params.get('task_id', '')
                    updates = []
                    if 'title' in tool_params:
                        updates.append(f"title to '{tool_params['title']}'")
                    if 'priority' in tool_params:
                        updates.append(f"priority to {tool_params['priority']}")
                    if 'due_date' in tool_params:
                        if tool_params['due_date']:
                            updates.append("due date")
                        else:
                            updates.append("removed due date")
                    if 'description' in tool_params:
                        updates.append("description")
                    if 'completed' in tool_params:
                        updates.append(f"completed status to {tool_params['completed']}")
                    
                    if updates:
                        response_text = f"I've updated task {task_id}: {', '.join(updates)}."
                    else:
                        response_text = f"I've updated task {task_id}."
                elif tool_name == 'delete_task':
                    task_id = tool_params.get('task_id', '')
                    response_text = f"I've removed task {task_id} from your tasks."
                elif tool_name == 'set_task_deadline':
                    task_id = tool_params.get('task_id', '')
                    due_date = tool_params.get('due_date')
                    if due_date:
                        response_text = f"I've updated the deadline for task {task_id}."
                    else:
                        response_text = f"I've removed the deadline from task {task_id}."
                elif tool_name == 'set_recurring':
                    task_id = tool_params.get('task_id', '')
                    pattern = tool_params.get('pattern', '')
                    end_date = tool_params.get('end_date')
                    if pattern == 'none':
                        response_text = f"I've stopped the recurrence for task {task_id}. It's now a one-time task."
                    elif end_date:
                        response_text = f"I've set task {task_id} to repeat {pattern} until {end_date}."
                    else:
                        response_text = f"I've set task {task_id} to repeat {pattern}."
                else:
                    response_text = "Done! Let me know if you need anything else."

                logger.warning(
                    f"Generated fallback response for empty AI response with tool calls",
                    extra={"user_id": user_id, "tool": tool_name}
                )

            logger.info(
                f"Agent response for user {user_id}: "
                f"{len(response_text)} chars, {len(tool_calls_data)} tool calls"
            )

        return AgentResponse(
            response=response_text,
            tool_calls=tool_calls_data
        )

    except TimeoutError as e:
        # OpenAI API timeout (T173)
        logger.error(
            "OpenAI API timeout",
            extra={
                "user_id": user_id,
                "error": str(e),
                "error_type": "timeout"
            },
            exc_info=True
        )
        return AgentResponse(
            response="I'm having trouble processing your request right now. Please try again in a moment.",
            tool_calls=[]
        )
    except AuthenticationError as e:
        # OpenAI API authentication error (invalid API key)
        logger.error(
            "OpenAI API authentication failed",
            extra={
                "user_id": user_id,
                "error": str(e),
                "error_type": "authentication_error"
            },
            exc_info=True
        )
        return AgentResponse(
            response="I'm experiencing a configuration issue. Please contact support.",
            tool_calls=[]
        )
    except RateLimitError as e:
        # OpenAI API rate limit exceeded
        logger.error(
            "OpenAI API rate limit exceeded",
            extra={
                "user_id": user_id,
                "error": str(e),
                "error_type": "rate_limit_error"
            },
            exc_info=True
        )
        return AgentResponse(
            response="I'm receiving too many requests right now. Please wait a moment and try again.",
            tool_calls=[]
        )
    except APIConnectionError as e:
        # OpenAI API connection error
        logger.error(
            "OpenAI API connection failed",
            extra={
                "user_id": user_id,
                "error": str(e),
                "error_type": "connection_error"
            },
            exc_info=True
        )
        return AgentResponse(
            response="I'm having trouble connecting to the AI service. Please check your internet connection and try again.",
            tool_calls=[]
        )
    except APIError as e:
        # General OpenAI API error
        error_msg = str(e)
        status_code = getattr(e, 'status_code', None)
        
        logger.error(
            f"OpenAI API error: {error_msg}",
            extra={
                "user_id": user_id,
                "error": error_msg,
                "error_type": "api_error",
                "status_code": status_code,
                "user_message_preview": message[:100] if message else None
            },
            exc_info=True
        )
        
        # Provide more specific error message based on status code
        if status_code == 429:
            return AgentResponse(
                response="I'm receiving too many requests right now. Please wait a moment and try again.",
                tool_calls=[]
            )
        elif status_code == 500 or status_code == 502 or status_code == 503:
            return AgentResponse(
                response="The AI service is temporarily unavailable. Please try again in a moment.",
                tool_calls=[]
            )
        else:
            return AgentResponse(
                response=f"I encountered an issue with the AI service (Error: {status_code or 'Unknown'}). Please try again in a moment.",
                tool_calls=[]
            )
    except ValueError as e:
        # Configuration or validation errors
        logger.error(
            "Configuration error in agent",
            extra={
                "user_id": user_id,
                "error": str(e),
                "error_type": "value_error"
            },
            exc_info=True
        )
        return AgentResponse(
            response="I'm experiencing a configuration issue. Please contact support.",
            tool_calls=[]
        )
    except Exception as e:
        # Generic error handling with user-friendly message (T175)
        error_type = type(e).__name__
        logger.error(
            "Agent execution failed",
            extra={
                "user_id": user_id,
                "error": str(e),
                "error_type": error_type
            },
            exc_info=True
        )
        return AgentResponse(
            response="I'm having trouble processing your request. Please try again.",
            tool_calls=[]
        )
