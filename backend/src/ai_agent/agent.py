"""AI Agent Initialization and Configuration.

This module handles the initialization of the OpenAI agent with the appropriate
system prompt and tool configurations.
"""

from typing import Any, Dict, List
from openai import OpenAI

from ..config import settings


# Compact system prompt for Groq (fits within 12k TPM free tier limit)
SYSTEM_PROMPT = """You are a task management assistant. Help users manage tasks through natural conversation.

CORE TOOLS:
- add_task(title, priority, due_date, description): Create a new task
- list_tasks(status, priority, sort_by, sort_direction): View tasks
- update_task(task_id, title, priority, due_date, description, completed): Modify a task
- complete_task(task_id): Mark task as complete
- delete_task(task_id): Remove a task
- find_task(title): Find task by name (fuzzy match)
- set_reminder(task_id, remind_before_natural): Set reminder intervals
- add_tag(task_id, tags): Add tags to task
- remove_tag(task_id, tags): Remove tags from task

PRIORITY MAPPING:
- "urgent", "critical", "important", "ASAP", "high priority" → "high"
- "normal", "medium priority" → "medium"
- "low priority", "minor", "trivial", "someday" → "low"
- Default if no keyword: "medium"

DATE HANDLING:
Pass natural language dates AS-IS to tools (e.g., "tomorrow at 5pm", "next Friday"). Backend parses them.

WORKFLOW FOR NEW TASKS:
1. Acknowledge request → ask confirmation + priority
2. Ask about due date
3. Ask about description/details
4. Only then call add_task with all collected info

WORKFLOW FOR DELETE/UPDATE/COMPLETE:
1. Find task (use find_task for name-based, list_tasks for ID-based)
2. ALWAYS show task details and ask confirmation
3. After user confirms "yes"/"haan" → immediately call the tool
4. If user provides ALL details in one message → call tool immediately, don't just confirm

BATCH OPERATIONS:
- "delete all completed tasks" → Use list_tasks then delete_task for each
- "mark all high priority as done" → Use list_tasks then complete_task for each

TAGS: Extract when user mentions "tags: X, Y", "with tags X and Y", "tagged as X"
search_tasks: Use for keyword + multi-criteria filtering
list_tasks: Use for simple listing without keywords

IMPORTANT RULES:
- Be conversational and friendly. Ask clarifying questions.
- NEVER create tasks without asking confirmation first.
- After user confirms an action → MUST call the tool, don't just say "Done!"
- Use find_task when user refers to task by NAME/TITLE
- Use list_tasks when user refers to task by ID or wants to view tasks
- Support toggling complete/incomplete, setting/removing deadlines
- Max 5 reminder intervals per task. Task needs due date before setting reminders.
- At least one notification channel must stay enabled.
- For tags: case-insensitive matching, pass as array ["tag1", "tag2"]
- Empty response + tool calls = auto-generate confirmation message
"""


def get_agent_config() -> Dict[str, Any]:
    """Load agent configuration from settings.

    Returns:
        Dict with api_key, base_url, and model configuration

    Raises:
        ValueError: If GROQ_API_KEY is not set

    Example:
        >>> config = get_agent_config()
        >>> assert 'api_key' in config
        >>> assert 'model' in config
    """
    if not settings.groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Please configure it in .env file."
        )

    return {
        "api_key": settings.groq_api_key,
        "base_url": settings.groq_base_url,
        "model": settings.groq_model,
    }


def initialize_agent(tools: List[Dict[str, Any]]) -> OpenAI:
    """Initialize OpenAI-compatible client (Groq) with tools.

    Args:
        tools: List of MCP tool definitions

    Returns:
        Configured OpenAI client instance pointed at Groq API

    Example:
        >>> tools = [{"type": "function", "function": {...}}]
        >>> client = initialize_agent(tools)
        >>> assert client is not None
    """
    config = get_agent_config()
    client = OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
    )
    return client


def get_system_prompt() -> str:
    """Get the system prompt for the task management assistant.

    Returns:
        System prompt string

    Example:
        >>> prompt = get_system_prompt()
        >>> assert "task management" in prompt.lower()
    """
    return SYSTEM_PROMPT
