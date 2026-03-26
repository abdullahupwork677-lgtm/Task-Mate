# Recurring Tasks - Demo Screenshots & Video Guide

**Visual demonstration of recurring tasks feature**

This document describes the screenshots and demo video that showcase the recurring tasks functionality.

---

## Demo Video Script (5 minutes)

### Scene 1: Introduction (30 seconds)

**Voiceover**: "Welcome to the Recurring Tasks feature! In this demo, we'll show you how to create tasks that automatically repeat on your schedule."

**Visual**:
- Show landing page
- Highlight "Phase V: Recurring Tasks" badge
- Quick overview of what we'll demo

---

### Scene 2: Creating a Daily Recurring Task (60 seconds)

**Voiceover**: "Let's start by creating a simple daily task. Watch how easy it is!"

**Actions**:
1. Navigate to Tasks page
2. Click "Add Task"
3. Enter title: "Morning standup"
4. Set priority: High
5. Toggle "Recurring" switch
6. Select pattern: "Daily"
7. Click "Create"

**Result**:
- Task appears with blue recurrence badge showing "🔄 daily"
- Task #1 in the list

**Screenshot 1**: Task creation form with recurring options
**Screenshot 2**: Task list showing task with recurrence badge

---

### Scene 3: Completing a Recurring Task (45 seconds)

**Voiceover**: "Now watch what happens when we complete a recurring task..."

**Actions**:
1. Click "Complete" on Task #1 "Morning standup"
2. Show success message: "Task completed. Next occurrence created."
3. Task #1 shows "Done" badge (green)
4. Task #2 appears automatically with due date = tomorrow

**Result**:
- Task #1: "Morning standup" [HIGH] [Done] [🔄 daily]
- Task #2: "Morning standup" [HIGH] [🔄 daily] (due tomorrow)

**Screenshot 3**: Task #1 marked complete with "Done" badge
**Screenshot 4**: Task #2 auto-created (next occurrence)

---

### Scene 4: Custom Intervals (60 seconds)

**Voiceover**: "Need a custom schedule? Try 'every 3 days' or 'every 2 weeks'..."

**Actions**:
1. Create new task: "Water plants"
2. Set recurrence: "every 3 days"
3. Complete task
4. Next occurrence created 3 days from now

**Result**:
- Recurrence badge shows "🔄 every 3 days"
- Next task scheduled 3 days later

**Screenshot 5**: Task with custom interval "every 3 days"

---

### Scene 5: AI Agent Integration (90 seconds)

**Voiceover**: "Or just tell the AI what you want in natural language!"

**Actions**:
1. Navigate to Chat page
2. Type: "Add a daily task 'Exercise'"
3. AI creates recurring task automatically
4. Type: "Make task 5 repeat weekly"
5. AI converts existing task to recurring
6. Type: "Stop repeating task 3"
7. AI cancels recurrence

**Chat Examples**:
```
You: Add a daily task 'Exercise'
AI: ✓ Created recurring task "Exercise" (repeats daily)

You: Make task 5 repeat weekly
AI: ✓ Task #5 "Grocery shopping" is now recurring (weekly)

You: Stop repeating task 3
AI: ✓ Task #3 "Old task" recurrence canceled
```

**Screenshot 6**: Chat interface showing natural language commands
**Screenshot 7**: AI response confirming task creation

---

### Scene 6: Recurrence End Dates (45 seconds)

**Voiceover**: "Need a task to stop after a certain date? Set an end date!"

**Actions**:
1. Create task: "Project standup"
2. Set recurrence: "daily"
3. Set end date: "2 weeks from now"
4. Complete task multiple times
5. After 14 completions → no more occurrences

**Result**:
- Final completion message: "Recurrence ended (reached end date)"
- No Task #15 created

**Screenshot 8**: Task creation with end date selected
**Screenshot 9**: Final completion showing "recurrence ended"

---

## Screenshot Specifications

### Screenshot 1: Task Creation Form
**File**: `demo-screenshots/01-create-recurring-task.png`

**Content**:
- Task form with fields:
  - Title: "Morning standup"
  - Description: ""
  - Priority: "High" (selected)
  - Due Date: "Tomorrow at 9am"
  - ☑ Recurring (checkbox checked)
  - Recurrence Pattern: "daily" (dropdown)
  - End Date: (empty)
- Highlight the "Recurring" checkbox and pattern dropdown
- Include "Create Task" button

---

### Screenshot 2: Task List with Recurrence Badge
**File**: `demo-screenshots/02-task-with-badge.png`

**Content**:
- Task list showing:
  - #42 Morning exercise [HIGH] [🔄 daily]
  - #43 Team review [MEDIUM] [🔄 weekly]
  - #44 Monthly report [HIGH] [🔄 monthly]
- Highlight the blue recurrence badges
- Show different patterns (daily, weekly, monthly)

---

### Screenshot 3: Completed Recurring Task
**File**: `demo-screenshots/03-completed-task.png`

**Content**:
- Task #42: "Morning standup" [HIGH] [Done] [🔄 daily]
- Show both green "Done" badge and blue recurrence badge
- Task title with strikethrough
- "Mark Incomplete" button visible

---

### Screenshot 4: Auto-Created Next Occurrence
**File**: `demo-screenshots/04-next-occurrence.png`

**Content**:
- Task list showing:
  - #42: "Morning standup" [HIGH] [Done] [🔄 daily] (today)
  - #43: "Morning standup" [HIGH] [🔄 daily] (tomorrow at 9am)
- Highlight that #43 has same title/pattern as #42
- Show due date difference (tomorrow)
- Emphasize "auto-created" annotation

---

### Screenshot 5: Custom Interval
**File**: `demo-screenshots/05-custom-interval.png`

**Content**:
- Task: "Water plants" [MEDIUM] [🔄 every 3 days]
- Recurrence pattern dropdown showing:
  - daily
  - weekly
  - monthly
  - yearly
  - every N days ← selected
- Input field: "3" days
- Next due date: "Feb 12, 2026"

---

### Screenshot 6: AI Chat Interface
**File**: `demo-screenshots/06-ai-chat.png`

**Content**:
```
Chat History:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You: Add a daily task 'Morning exercise'

AI: ✓ I've created a recurring task for you:
    • Task #42: "Morning exercise"
    • Recurrence: daily
    • Priority: medium
    • Due: Tomorrow at 9:00am

    Would you like to adjust the priority or due time?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You: Make task 10 repeat weekly

AI: ✓ Task #10 "Grocery shopping" is now recurring:
    • Pattern changed from "one-time" to "weekly"
    • Next occurrence will be created when you complete it
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Screenshot 7: Frontend Display (Mobile)
**File**: `demo-screenshots/07-mobile-view.png`

**Content**:
- Mobile view (375px width)
- Task list with recurring badges
- Responsive layout
- Touch-friendly buttons
- Badges wrap properly on small screens

---

### Screenshot 8: Recurrence End Date
**File**: `demo-screenshots/08-end-date.png`

**Content**:
- Task creation form:
  - Title: "Project standup"
  - Recurrence: "daily"
  - End Date: "2026-02-23" (2 weeks from now)
  - Calendar picker visible
- Annotation: "This task will stop repeating after Feb 23"

---

### Screenshot 9: Recurrence Ended Message
**File**: `demo-screenshots/09-recurrence-ended.png`

**Content**:
- Success toast/alert:
  ```
  ✓ Task #56 "Project standup" completed
  ℹ Recurrence ended (reached end date: 2026-02-23)
  No next occurrence created.
  ```
- Highlight the "recurrence ended" message
- Show Task #56 with [Done] badge but no Task #57

---

### Screenshot 10: Backend API Documentation
**File**: `demo-screenshots/10-api-docs.png`

**Content**:
- Swagger UI showing `/api/tasks` endpoints:
  - POST /api/tasks (with recurrence fields)
  - PATCH /api/tasks/{id} (complete task)
  - GET /api/tasks (list with recurring filter)
- Expand recurrence_pattern schema:
  - type: string
  - enum: ["daily", "weekly", "monthly", "yearly"]
  - pattern: "^every \\d+ (days|weeks|months)$"

---

## Demo Video Outline (Detailed)

### Equipment Needed
- Screen recording software (OBS, Loom, or QuickTime)
- Microphone for voiceover
- Video editing software (iMovie, DaVinci Resolve)

### Recording Steps

1. **Prepare Environment**
   - Clean browser cache
   - Start backend server
   - Create fresh test user
   - Reset database to clean state

2. **Record Scenes**
   - Record each scene separately
   - Use 1080p resolution (1920x1080)
   - Record at 30 FPS
   - Leave 2-second pauses between actions

3. **Post-Production**
   - Add voiceover narration
   - Add annotations/callouts
   - Add background music (subtle)
   - Add chapter markers
   - Export as MP4 (H.264, 720p or 1080p)

4. **Final Checks**
   - Verify audio quality
   - Check all text is readable
   - Ensure smooth transitions
   - Total length: 5-7 minutes

---

## Screenshot Capture Instructions

### Tools
- Chrome DevTools (for responsive screenshots)
- Snagit or built-in screenshot tools
- Image editor for annotations

### Settings
- **Desktop**: 1440x900 (MacBook Pro 13")
- **Mobile**: 375x667 (iPhone SE)
- **Format**: PNG (for UI) or JPG (for photos)
- **DPI**: 144 (2x retina)

### Capture Workflow

1. **Navigate to target page**
2. **Perform action** (e.g., create task)
3. **Capture screenshot** (Cmd+Shift+4 on Mac)
4. **Annotate** (if needed):
   - Add arrows pointing to key features
   - Add text labels
   - Highlight important elements
5. **Save** with descriptive filename
6. **Optimize** (compress without quality loss)

---

## Distribution

### Video Hosting
- **YouTube**: Public demo video
- **Vimeo**: Embedded in documentation
- **Loom**: Quick internal sharing

### Screenshot Storage
- **Repository**: `docs/screenshots/` (for README embedding)
- **Cloud**: Google Drive or Imgur (for larger files)
- **Documentation**: Embed in user guide and README

---

## Validation Checklist

- [ ] All 10 screenshots captured
- [ ] Screenshots show different recurring patterns
- [ ] Mobile and desktop views included
- [ ] AI chat examples captured
- [ ] Video recorded (5-7 minutes)
- [ ] Video includes voiceover
- [ ] Video has chapter markers
- [ ] All media optimized for web
- [ ] Screenshots embedded in README.md
- [ ] Video link added to documentation

---

## Example README.md Integration

```markdown
## Recurring Tasks Demo

### Daily Recurring Task
![Task with daily recurrence badge](docs/screenshots/02-task-with-badge.png)

### Auto-Created Next Occurrence
![Next occurrence automatically created](docs/screenshots/04-next-occurrence.png)

### AI Agent Natural Language
![AI understands "Add a daily task"](docs/screenshots/06-ai-chat.png)

### Full Demo Video
[![Watch full demo](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)
```

---

**Status**: 📋 Ready for Manual Creation
**Tools**: OBS Studio, Snagit, Chrome DevTools
**Estimated Time**: 3-4 hours (screenshots + video)

**Next Steps**:
1. Set up clean test environment
2. Record screenshots (1 hour)
3. Record demo video (2 hours)
4. Edit and export (1 hour)
5. Upload and embed in documentation

---

**Last Updated**: 2026-02-09
**Phase**: V (Recurring Tasks)
**Note**: This document serves as a blueprint. Actual screenshots and video to be created manually.
