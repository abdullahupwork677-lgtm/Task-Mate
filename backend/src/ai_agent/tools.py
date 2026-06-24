"""MCP Tool Registration for AI Agent.

This module registers MCP tools with the AI agent, providing tool definitions
with descriptions and parameter schemas.
"""

from typing import Any, Dict, List


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Get OpenAI function calling tool definitions for all MCP tools.

    Returns:
        List of tool definitions in OpenAI function calling format

    OpenAI Function Calling Format:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "What the tool does",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        }

    Example:
        >>> tools = get_tool_definitions()
        >>> assert isinstance(tools, list)
        >>> assert len(tools) > 0
    """
    tools = [
        # Phase 3: add_task tool (Phase 8: Extended with recurrence support)
        {
            "type": "function",
            "function": {
                "name": "add_task",
                "description": (
                    "Create a new task for the user. Supports both one-time and recurring tasks. "
                    "Use this when the user wants to add, create, remember, or note something. "
                    "Examples: 'Add task to buy milk', 'Remember to call mom', 'Create task: finish report', "
                    "'Add a daily task Morning exercise', 'Add recurring task Pay rent every month'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the authenticated user (automatically provided)",
                        },
                        "title": {
                            "type": "string",
                            "description": (
                                "Task title (1-200 characters). Extract the main "
                                "task from user's message. Examples: 'Buy milk', "
                                "'Call mom', 'Finish report', 'Morning exercise'."
                            ),
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "Optional task description with additional details. "
                                "Use when user provides extra context. "
                                "Example: 'quarterly sales report for Q4'."
                            ),
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": (
                                "Task priority level. CRITICAL: Extract from user's message. "
                                "Keywords mapping (YOU MUST USE THESE EXACTLY): "
                                "'urgent', 'critical', 'important', 'ASAP', 'high priority' → 'high', "
                                "'normal', 'medium priority' → 'medium', "
                                "'minor', 'trivial', 'low priority', 'someday' → 'low'. "
                                "ONLY use default 'medium' if NO priority keyword found in message. "
                                "If user says 'high priority', you MUST return 'high', NOT 'medium'!"
                            ),
                        },
                        "due_date": {
                            "type": "string",
                            "description": (
                                "Task due date in NATURAL LANGUAGE (Phase V - US1). "
                                "CRITICAL: Extract exactly as user says it - DO NOT convert to ISO format! "
                                "Examples: 'tomorrow', 'tomorrow at 5pm', 'next Friday', 'Feb 15 at 2pm', "
                                "'in 3 days', 'next week'. "
                                "Optional - only include if user specifies a deadline."
                            ),
                        },
                        "remind_before_natural": {
                            "type": "string",
                            "description": (
                                "Reminder intervals in natural language (Phase V - US1). "
                                "Extract if user mentions when to be reminded. "
                                "Examples: '24 hours before', '1 day before and 1 hour before', "
                                "'3 days before, 1 hour before'. "
                                "Optional - defaults to '24 hours before' and '1 hour before' if not specified."
                            ),
                        },
                        "user_timezone": {
                            "type": "string",
                            "description": (
                                "User's IANA timezone (e.g., 'America/New_York', 'Europe/London'). "
                                "Optional - defaults to 'UTC' if not provided. Use for accurate date parsing."
                            ),
                        },
                        "recurrence_pattern": {
                            "type": "string",
                            "description": (
                                "Recurrence pattern for recurring tasks (Phase 8 extension). "
                                "CRITICAL: Extract from user's message when they mention repetition. "
                                "Supported patterns: "
                                "'daily' - repeat every day (keywords: 'daily', 'every day'), "
                                "'weekly' - repeat every week (keywords: 'weekly', 'every week'), "
                                "'monthly' - repeat every month (keywords: 'monthly', 'every month'), "
                                "'yearly' - repeat every year (keywords: 'yearly', 'every year', 'annually'), "
                                "'every N days' - custom interval (e.g., 'every 3 days'), "
                                "'every N weeks' - custom interval (e.g., 'every 2 weeks'), "
                                "'every N months' - custom interval (e.g., 'every 6 months'). "
                                "Examples: 'Add a daily task Exercise' → 'daily', "
                                "'Add recurring task Pay rent every month' → 'monthly', "
                                "'Add task Water plants every 3 days' → 'every 3 days'. "
                                "Omit if task is one-time (not recurring)."
                            ),
                        },
                        "recurrence_end_date": {
                            "type": "string",
                            "description": (
                                "Optional end date for recurrence (natural language or ISO format). "
                                "Extract if user mentions when recurrence should stop. "
                                "Examples: 'Add a daily task Workout until March 31' → 'March 31', "
                                "'Add task Exercise daily until next month' → 'next month'. "
                                "Omit if user doesn't specify end date (infinite recurrence)."
                            ),
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Optional tags for task categorization (Phase V - US1 003-task-tags). "
                                "Extract if user mentions tags, categories, or labels. "
                                "Examples: 'add task buy groceries, tags: shopping, groceries' → ['shopping', 'groceries'], "
                                "'add task meeting with work and urgent tags' → ['work', 'urgent'], "
                                "'create task tagged with personal and health' → ['personal', 'health']. "
                                "Tags are normalized to lowercase and duplicates are removed. "
                                "Valid tags: 1-50 characters, alphanumeric with hyphens/underscores only."
                            ),
                        },
                    },
                    "required": ["title"],
                },
            },
        },
        # Phase 4: list_tasks tool (Phase V: added recurring filter)
        {
            "type": "function",
            "function": {
                "name": "list_tasks",
                "description": (
                    "List tasks for the user with optional filtering by completion status and recurrence. "
                    "Use this when the user wants to see, show, view, or list their tasks. "
                    "Examples: 'Show my tasks', 'What's pending?', 'List completed tasks', "
                    "'Show recurring tasks', 'What do I need to do?'"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the authenticated user (automatically provided)",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["all", "pending", "completed"],
                            "description": (
                                "Filter tasks by completion status. "
                                "'all' - show all tasks (default), "
                                "'pending' - show only incomplete tasks, "
                                "'completed' - show only finished tasks. "
                                "Examples: 'Show my tasks' → 'all', "
                                "'What's pending?' → 'pending', "
                                "'Show completed' → 'completed'."
                            ),
                        },
                        "recurring": {
                            "type": "string",
                            "enum": ["all", "recurring", "non-recurring"],
                            "description": (
                                "Filter tasks by recurring status (Phase V). "
                                "'all' - show all tasks (default), "
                                "'recurring' - show only recurring tasks, "
                                "'non-recurring' - show only one-time tasks. "
                                "Examples: 'Show recurring tasks' → 'recurring', "
                                "'List my regular tasks' → 'non-recurring', "
                                "'Show all tasks' → 'all'."
                            ),
                        },
                        "user_timezone": {
                            "type": "string",
                            "description": (
                                "User's IANA timezone for displaying due dates (Phase V - US1). "
                                "Optional - defaults to 'UTC'. Use user's timezone for readable date formatting."
                            ),
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["all", "high", "medium", "low"],
                            "description": (
                                "Filter tasks by priority level. "
                                "'all' - show all priorities (default), "
                                "'high' - show only high priority tasks, "
                                "'medium' - show only medium priority tasks, "
                                "'low' - show only low priority tasks. "
                                "Examples: 'Show high priority tasks' → 'high', "
                                "'List my urgent tasks' → 'high', "
                                "'Show low priority items' → 'low'."
                            ),
                        },
                        "tag_filter": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Filter tasks by tags with OR logic (Phase V - US3 003-task-tags). "
                                "Returns tasks that have ANY of the specified tags. "
                                "Examples: 'show work tasks' → ['work'], "
                                "'list shopping and groceries tasks' → ['shopping', 'groceries'], "
                                "'show work or urgent tasks' → ['work', 'urgent']. "
                                "Tags are normalized to lowercase for matching. "
                                "Omit to show all tasks regardless of tags."
                            ),
                        },
                    },
                    "required": [],
                },
            },
        },
        # Phase 5: complete_task tool
        {
            "type": "function",
            "function": {
                "name": "complete_task",
                "description": (
                    "Mark a task as completed. "
                    "Use this when the user says they finished, completed, or are done with a task. "
                    "Examples: 'Mark task 5 as complete', 'I finished buying milk', "
                    "'Done with calling mom', 'Complete task 3'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the authenticated user (automatically provided)",
                        },
                        "task_id": {
                            "type": "integer",
                            "description": (
                                "ID of the task to mark as complete. "
                                "Extract from user's message (e.g., 'Mark task 5 as complete' → 5). "
                                "If user mentions task by title instead of ID, first call list_tasks "
                                "to find the task_id, then call complete_task."
                            ),
                        },
                    },
                    "required": ["task_id"],
                },
            },
        },
        # Phase 6: update_task tool
        {
            "type": "function",
            "function": {
                "name": "update_task",
                "description": (
                    "Update a task's title or description. "
                    "Use this when the user wants to change, edit, modify, or update a task. "
                    "Examples: 'Change task 3 to Buy milk and eggs', "
                    "'Update description of task 2 to include deadline', "
                    "'Edit task 5 title to Call mom tomorrow'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the authenticated user (automatically provided)",
                        },
                        "task_id": {
                            "type": "integer",
                            "description": "ID of the task to update",
                        },
                        "title": {
                            "type": "string",
                            "description": "New task title (optional, provide if user wants to change title)",
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "New task description (optional, provide if user wants "
                                "to change description)"
                            ),
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": (
                                "New task priority (optional, provide if user wants to change priority). "
                                "Extract from user's message using keywords: "
                                "'high priority', 'urgent', 'important' → 'high', "
                                "'medium priority', 'normal' → 'medium', "
                                "'low priority', 'minor' → 'low'. "
                                "If user says 'change to high priority', you MUST use 'high'!"
                            ),
                        },
                        "due_date": {
                            "type": "string",
                            "description": (
                                "New task due date in NATURAL LANGUAGE (Phase V - US1). "
                                "CRITICAL: Extract exactly as user says it - DO NOT convert to ISO format! "
                                "Examples: 'tomorrow at 5pm', 'next Friday', 'Feb 15 at 2pm'. "
                                "Optional - provide if user wants to change or set deadline."
                            ),
                        },
                        "clear_due_date": {
                            "type": "boolean",
                            "description": (
                                "Set to true to REMOVE the due date completely (Phase V - US1). "
                                "Use when user says 'remove deadline', 'clear due date', 'no deadline'. "
                                "Examples: 'Remove deadline from task 5' → true"
                            ),
                        },
                        "user_timezone": {
                            "type": "string",
                            "description": (
                                "User's IANA timezone (e.g., 'America/New_York', 'Europe/London'). "
                                "Optional - defaults to 'UTC' if not provided."
                            ),
                        },
                        "completed": {
                            "type": "boolean",
                            "description": (
                                "Mark task as complete (true) or incomplete (false). "
                                "Use this to toggle completion status. "
                                "Examples: 'mark as incomplete' → false, 'mark as done' → true"
                            ),
                        },
                    },
                    "required": ["task_id"],
                },
            },
        },
        # Phase 7: delete_task tool
        {
            "type": "function",
            "function": {
                "name": "delete_task",
                "description": (
                    "Delete a task permanently. "
                    "Use this when the user wants to remove, delete, or get rid of a task. "
                    "Examples: 'Delete task 7', 'Remove the milk task', "
                    "'Get rid of task 3', 'Delete my task about calling mom'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the authenticated user (automatically provided)",
                        },
                        "task_id": {
                            "type": "integer",
                            "description": (
                                "ID of the task to delete. "
                                "If user mentions task by title, first call list_tasks "
                                "to find the task_id, then call delete_task."
                            ),
                        },
                    },
                    "required": ["task_id"],
                },
            },
        },
        # find_task tool for task lookup by title
        {
            "type": "function",
            "function": {
                "name": "find_task",
                "description": (
                    "Find a task by its title for the authenticated user. "
                    "Use this when the user refers to a task by name/title instead of ID, "
                    "especially when they want to update or delete a task. "
                    "Examples: 'Find the task about buy book', 'Look up task titled Buy milk', "
                    "'Search for task Call mom'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the authenticated user (automatically provided)",
                        },
                        "title": {
                            "type": "string",
                            "description": "Task title to search for (case-insensitive partial match)",
                        },
                    },
                    "required": ["title"],
                },
            },
        },



        # Phase V - US4: set_reminder tool for custom reminder intervals
        {
            "type": "function",
            "function": {
                "name": "set_reminder",
                "description": (
                    "Set custom reminder intervals for a task using natural language. "
                    "Use this when the user wants to customize when they receive reminders before a task is due. "
                    "Supports multiple intervals with natural language like '3 days before', '1 hour before'. "
                    "Examples: 'Remind me about task 5 three days before and 1 hour before', "
                    "'Set reminder for task 3 one week before', 'Clear all reminders for task 7'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the authenticated user (automatically provided)",
                        },
                        "task_id": {
                            "type": "integer",
                            "description": "ID of the task to set reminders for",
                        },
                        "remind_before_natural": {
                            "type": "string",
                            "description": (
                                "Reminder intervals in natural language (Phase V - US4). "
                                "CRITICAL: Extract exactly from user's message. "
                                "Supports: minutes (e.g., '30 minutes before'), "
                                "hours (e.g., '1 hour before'), days (e.g., '3 days before'), "
                                "weeks (e.g., '1 week before'). "
                                "Multiple intervals: '3 days before and 1 hour before', "
                                "'1 week, 3 days, and 1 hour before'. "
                                "Maximum 5 intervals allowed. "
                                "Empty string to clear all reminders. "
                                "Examples: '3 days before and 1 hour before' → ['3d', '1h'], "
                                "'remind me 1 week before' → ['1w'], "
                                "'clear all reminders' → ''."
                            ),
                        },
                    },
                    "required": ["task_id", "remind_before_natural"],
                },
            },
        },


        # Phase V - US2 (003-task-tags): add_tag tool for adding tags to existing tasks
        {
            "type": "function",
            "function": {
                "name": "add_tag",
                "description": (
                    "Add tags to an existing task for categorization and organization. "
                    "Use this when the user wants to tag, label, or categorize an existing task. "
                    "Supports multiple tags and deduplicates if tag already exists. "
                    "Examples: 'Add tag urgent to task 5', 'Tag task 3 with work and important', "
                    "'Add tags shopping and groceries to task 7'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the authenticated user (automatically provided)",
                        },
                        "task_id": {
                            "type": "integer",
                            "description": "ID of the task to add tags to",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Array of tags to add (e.g., ['urgent', 'work']). "
                                "Tags will be normalized to lowercase and deduplicated. "
                                "Valid tags: 1-50 characters, alphanumeric with hyphens/underscores only. "
                                "Examples: 'add tag urgent' → ['urgent'], "
                                "'tag with work and important' → ['work', 'important']"
                            ),
                        },
                    },
                    "required": ["task_id", "tags"],
                },
            },
        },
        # Phase V - US2 (003-task-tags): remove_tag tool for removing tags from existing tasks
        {
            "type": "function",
            "function": {
                "name": "remove_tag",
                "description": (
                    "Remove tags from an existing task. "
                    "Use this when the user wants to untag, remove labels, or delete tags from a task. "
                    "Case-insensitive matching - 'Work' matches 'work'. "
                    "Examples: 'Remove tag urgent from task 5', 'Untag task 3 from work', "
                    "'Delete tags shopping and groceries from task 7'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the authenticated user (automatically provided)",
                        },
                        "task_id": {
                            "type": "integer",
                            "description": "ID of the task to remove tags from",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Array of tags to remove (e.g., ['urgent', 'work']). "
                                "Tags will be normalized for case-insensitive matching. "
                                "Examples: 'remove tag urgent' → ['urgent'], "
                                "'untag from work and important' → ['work', 'important']"
                            ),
                        },
                    },
                    "required": ["task_id", "tags"],
                },
            },
        },


    ]

    return tools


def register_tools() -> List[Dict[str, Any]]:
    """Register all MCP tools with the AI agent.

    Returns:
        List of registered tool definitions

    Implemented tools:
    - add_task (Create tasks with natural language)
    - list_tasks (View and filter tasks)
    - complete_task (Mark tasks complete)
    - update_task (Modify task details)
    - delete_task (Remove tasks)
    - find_task (Search tasks by name)
    - set_reminder (Set reminder intervals)
    - add_tag (Add tags to tasks)
    - remove_tag (Remove tags from tasks)

    Example:
        >>> tools = register_tools()
        >>> assert isinstance(tools, list)
        >>> assert len(tools) == 9  # 9 task management tools
    """
    return get_tool_definitions()
