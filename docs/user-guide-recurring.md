# User Guide: Recurring Tasks

**Welcome to Recurring Tasks!** This guide will help you create and manage tasks that repeat automatically.

---

## Table of Contents

1. [What are Recurring Tasks?](#what-are-recurring-tasks)
2. [Quick Start](#quick-start)
3. [Creating Recurring Tasks](#creating-recurring-tasks)
4. [Completing Recurring Tasks](#completing-recurring-tasks)
5. [Modifying Recurring Tasks](#modifying-recurring-tasks)
6. [Canceling Recurrence](#canceling-recurrence)
7. [Common Patterns](#common-patterns)
8. [FAQ](#faq)
9. [Troubleshooting](#troubleshooting)

---

## What are Recurring Tasks?

Recurring tasks are tasks that repeat automatically on a schedule. When you complete a recurring task, the app automatically creates the next occurrence for you.

**Perfect for:**
- Daily routines (exercise, standup meetings, morning coffee)
- Weekly activities (team reviews, grocery shopping, laundry)
- Monthly chores (rent payment, reports, car maintenance)
- Custom schedules (water plants every 3 days, visit dentist every 6 months)

**Benefits:**
- ✅ Never forget repetitive tasks
- ✅ Automatically schedules next occurrence
- ✅ Keeps your task list organized
- ✅ Works with natural language (just talk to the AI!)

---

## Quick Start

### Method 1: Create Recurring Task in One Command

Simply tell the AI what you want:

```
You: "Add a daily task 'Morning exercise'"
AI: ✓ Created recurring task "Morning exercise" (repeats daily)

You: "Create a weekly team meeting"
AI: ✓ Created recurring task "Team meeting" (repeats weekly)

You: "Add a monthly report task"
AI: ✓ Created recurring task "Monthly report" (repeats monthly)
```

### Method 2: Make Existing Task Recurring

Already have a task? Make it recurring:

```
You: "Make task 5 repeat daily"
AI: ✓ Task #5 "Buy groceries" is now recurring (daily)

You: "Set task 10 to repeat every week"
AI: ✓ Task #10 "Team sync" is now recurring (weekly)
```

---

## Creating Recurring Tasks

### Basic Patterns

The AI understands these simple patterns:

| What You Say | What You Get |
|--------------|--------------|
| "Add a **daily** task 'X'" | Repeats every day |
| "Create a **weekly** task 'X'" | Repeats every week |
| "Add a **monthly** task 'X'" | Repeats every month |
| "Create a **yearly** task 'X'" | Repeats every year |

**Examples:**
```
✓ "Add a daily task 'Morning standup'"
✓ "Create a weekly grocery shopping task"
✓ "Add a monthly rent payment reminder"
✓ "Create a yearly tax filing task"
```

### Custom Intervals

Need a different schedule? Use custom intervals:

| What You Say | What You Get |
|--------------|--------------|
| "**every 3 days**" | Repeats every 3 days |
| "**every 2 weeks**" | Repeats every 2 weeks |
| "**every 6 months**" | Repeats every 6 months |

**Examples:**
```
✓ "Add a task 'Water plants' every 3 days"
✓ "Create a task 'Team retrospective' every 2 weeks"
✓ "Add a task 'Dentist checkup' every 6 months"
```

### With End Dates

Want the task to stop repeating after a certain date?

```
✓ "Add a daily task 'Project standup' until next month"
✓ "Create a weekly review task for 3 months"
✓ "Add a monthly report until end of year"
✓ "Create a task 'Take vitamins' daily for 90 days"
```

**The AI understands:**
- "until next month"
- "for 3 months"
- "until end of year"
- "for 90 days"
- "until 2027-12-31"

---

## Completing Recurring Tasks

### How It Works

1. **Complete the task** as usual:
   ```
   You: "Complete task 5"
   AI: ✓ Task #5 "Morning exercise" completed
       ✓ Next occurrence created: Task #6 (due tomorrow)
   ```

2. **Next occurrence is auto-created**:
   - Inherits the task title
   - Inherits the description
   - Inherits the priority
   - Scheduled for next occurrence date
   - Links back to original task

3. **Repeat** as many times as you want!

### Visual Example

```
Day 1:
  Task #5: "Morning exercise" (daily) → Complete ✓
  → Task #6: "Morning exercise" (due tomorrow) created automatically

Day 2:
  Task #6: "Morning exercise" (daily) → Complete ✓
  → Task #7: "Morning exercise" (due tomorrow) created automatically

Day 3:
  Task #7: "Morning exercise" (daily) → Complete ✓
  → Task #8: "Morning exercise" (due tomorrow) created automatically
```

### What Happens When End Date is Reached?

```
You: "Complete task 5"
AI: ✓ Task #5 "Temporary project task" completed
    ℹ Recurrence ended (reached end date: 2026-12-31)
    No next occurrence created
```

---

## Modifying Recurring Tasks

### Change Recurrence Pattern

```
You: "Change task 5 to repeat every 2 days"
AI: ✓ Task #5 recurrence updated (every 2 days)

You: "Make task 10 monthly instead of weekly"
AI: ✓ Task #10 recurrence updated (monthly)
```

### Add End Date to Existing Recurring Task

```
You: "Set task 5 to stop repeating after next month"
AI: ✓ Task #5 will stop recurring after 2026-03-31
```

### Change End Date

```
You: "Extend task 5 recurrence until end of year"
AI: ✓ Task #5 end date updated (2026-12-31)
```

---

## Canceling Recurrence

Want to stop a task from repeating?

```
You: "Stop repeating task 5"
AI: ✓ Task #5 "Morning exercise" is no longer recurring

You: "Cancel recurrence for task 10"
AI: ✓ Task #10 recurrence canceled

You: "Make task 7 non-recurring"
AI: ✓ Task #7 is now a one-time task
```

**Note:** This doesn't delete the task, it just stops it from creating new occurrences.

---

## Common Patterns

### Daily Routines

```
✓ "Add a daily task 'Morning standup at 9am'"
✓ "Create a daily exercise reminder"
✓ "Add a daily medication reminder"
✓ "Create a daily journal entry task"
```

### Weekly Activities

```
✓ "Add a weekly grocery shopping task"
✓ "Create a weekly team meeting"
✓ "Add a weekly house cleaning task"
✓ "Create a weekly one-on-one with manager"
```

### Monthly Chores

```
✓ "Add a monthly rent payment reminder"
✓ "Create a monthly budget review task"
✓ "Add a monthly report task"
✓ "Create a monthly car maintenance reminder"
```

### Custom Schedules

```
✓ "Add a task 'Water plants' every 3 days"
✓ "Create a task 'Backup data' every 2 weeks"
✓ "Add a task 'Oil change' every 3 months"
✓ "Create a task 'Dentist checkup' every 6 months"
```

### Temporary Recurring Tasks

```
✓ "Add a daily standup task for this project sprint (2 weeks)"
✓ "Create a weekly review task for the next 3 months"
✓ "Add a daily medication task for 30 days"
```

---

## FAQ

### Q: What happens if I don't complete a recurring task on time?

**A:** The task stays in your list until you complete it. When you complete it, the next occurrence is created based on the original schedule (not from the completion date).

**Example:**
- Task due: Monday 9am (daily)
- You complete it: Wednesday 3pm
- Next occurrence: Tuesday 9am (not Thursday!)

### Q: Can I have multiple occurrences of the same task?

**A:** No. The app ensures only one active occurrence exists at a time. When you complete one, the next is created. This prevents duplicate tasks.

### Q: What if I complete a task twice by mistake?

**A:** The app prevents this! If you try to complete an already-completed task, you'll get an error message.

### Q: Can I edit a recurring task's title or description?

**A:** Yes! Edit the task as normal. However, changes only apply to that specific occurrence. Future occurrences will have the original title/description.

**Note:** If you want all future occurrences to have the new title, edit the most recent occurrence before completing it.

### Q: How do I see all occurrences of a recurring task?

**A:** Each occurrence has a `parent_task_id` field that links back to the original task. You can filter by this field to see the history.

### Q: Can I have a task repeat on specific days of the week?

**A:** Currently, the app supports interval-based recurrence (every N days/weeks/months). Specific day-of-week scheduling (e.g., "every Monday and Wednesday") is coming in a future update!

### Q: What happens if I delete a recurring task?

**A:** Deleting a recurring task permanently removes it. It will NOT create a next occurrence. If you want to pause it instead, use "stop repeating" to cancel recurrence.

### Q: Can I complete future occurrences in advance?

**A:** The app is designed for completing tasks as they come due. Completing future occurrences in advance is not recommended, as it may create scheduling confusion.

---

## Troubleshooting

### "Invalid recurrence pattern" Error

**Problem:** The AI doesn't understand your recurrence pattern.

**Solution:** Use one of the supported patterns:
- Simple: "daily", "weekly", "monthly", "yearly"
- Custom: "every 3 days", "every 2 weeks", "every 6 months"

**Examples:**
```
✗ "Add a task repeating every other day"  (use "every 2 days" instead)
✓ "Add a task every 2 days"

✗ "Add a task on Mondays and Wednesdays"  (not yet supported)
✓ "Add a weekly task"  (then adjust due date manually)
```

### Task Not Auto-Creating Next Occurrence

**Possible Causes:**

1. **Task is not marked as recurring**
   - Check: Does the task have a blue recurrence badge?
   - Fix: "Make task recurring [pattern]"

2. **Recurrence end date reached**
   - Check: Has the end date passed?
   - Fix: Extend end date or remove it

3. **Task has no due date**
   - Check: Does the task have a due date?
   - Note: Next occurrence uses completion date if no due date exists

### "Task already completed" Error

**Problem:** You're trying to complete a task that's already marked complete.

**Solution:** Check the task list. Look for the next occurrence (it may have a higher task ID).

**Example:**
```
✗ "Complete task 5"  (if #5 is already done)
✓ "Complete task 6"  (next occurrence)
```

### Recurrence Stopped Unexpectedly

**Possible Causes:**

1. **End date reached**
   - Check: What was the end date?
   - Fix: Remove or extend end date

2. **Recurrence canceled**
   - Check: Is `is_recurring` still true?
   - Fix: Set recurrence again

3. **Task deleted**
   - Check: Does the task still exist?
   - Fix: Create a new recurring task

---

## Tips & Best Practices

### Tip 1: Use Descriptive Titles

```
✓ "Daily standup at 9am"
✓ "Weekly team review (Fridays)"
✓ "Monthly budget review - 1st of month"

✗ "Meeting"
✗ "Task"
✗ "TODO"
```

### Tip 2: Set Due Dates for Time-Sensitive Tasks

```
You: "Add a daily task 'Morning standup' at 9am"
AI: ✓ Created recurring task with due date 9:00am
```

### Tip 3: Use Priorities

```
You: "Add a high priority weekly team meeting"
AI: ✓ Created recurring task (priority: high)
```

### Tip 4: Add Descriptions for Context

```
You: "Add a monthly report task with description 'Include sales, expenses, and projections'"
AI: ✓ Created recurring task with description
```

### Tip 5: Review Recurring Tasks Regularly

Check your recurring tasks once a month:
- Are they still relevant?
- Should frequencies be adjusted?
- Should any be canceled?

---

## Need Help?

- **API Documentation**: `backend/docs/api.md` (technical details)
- **Backend README**: `backend/README.md` (developer guide)
- **Quickstart**: `specs/Phase-5/001-recurring-tasks/quickstart.md` (quick examples)
- **Support**: Open an issue on GitHub

---

**Happy Recurring!** 🔄

Never forget a repetitive task again. Let the app handle the scheduling while you focus on getting things done.

---

**Last Updated**: 2026-02-09
**Version**: Phase V (Recurring Tasks)
**Status**: ✅ Complete
