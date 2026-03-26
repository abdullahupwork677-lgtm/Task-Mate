# Frontend - Todo Chatbot Phase 3

> **Next.js 14 + TypeScript + Tailwind CSS + OpenAI ChatKit**
> Modern, responsive web application with AI-powered natural language task management

---

## 📋 Table of Contents

- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Frontend Agents](#frontend-agents)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Components](#components)
- [Pages & Routes](#pages--routes)
- [API Integration](#api-integration)
- [Authentication](#authentication)
- [Styling & Design](#styling--design)
- [Testing](#testing)
- [Deployment](#deployment)
- [Resources](#resources)

---

## 🎯 Overview

The **Frontend** is a Next.js 14 application built with TypeScript, Tailwind CSS, and shadcn/ui components. It provides a modern, responsive user interface for task management with AI-powered natural language interaction.

**Key Features:**
- ✅ User authentication (JWT-based)
- ✅ Task CRUD operations with traditional UI
- ✅ AI Chatbot for natural language task management
- ✅ Real-time conversation history
- ✅ Responsive design (mobile-first)
- ✅ Dark mode support
- ✅ Accessibility (WCAG AA compliant)
- ✅ Performance optimized (Core Web Vitals)

**Phase III Addition:**
- 🤖 **AI Chatbot Interface** - Natural language task management via OpenAI ChatKit
- 💬 **Conversation History** - Persistent chat sessions stored in PostgreSQL
- 🔄 **Seamless Integration** - Traditional UI + AI Chat in one cohesive experience

**Phase V Addition:**
- ⏰ **Due Date Badge** - Visual due date indicators with color-coded urgency
- 📅 **date-fns Integration** - Powerful date formatting and manipulation library
- 🔔 **Reminder Indicators** - Show when reminders are set (24h, 1h, custom)
- 🎨 **Status Badges** - Overdue, due soon, upcoming indicators
- 🏷️ **Task Tags & Categories** - Color-coded tag badges with autocomplete input
- 🎨 **TagBadge Component** - Deterministic color generation for consistent tag display
- ✍️ **TagInput Component** - Tag entry with autocomplete suggestions and keyboard navigation
- 🔍 **useTags Hook** - React hook for tag management state and operations
- 🌍 **Timezone Display** - Show dates in user's local timezone
- 🔎 **Task Search & Advanced Filtering** - Multi-criteria search with keyword, status, priority, tags, and due date filters
- 📄 **Pagination** - Page-based navigation for large result sets
- ✨ **Keyword Highlighting** - Visual highlighting of search terms in results
- 📊 **Result Summaries** - Human-readable descriptions of active filters
- 🚫 **Empty States** - Friendly messages when no results found

---

## 🛠️ Technology Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | Next.js 14 (App Router) | React framework with SSR/SSG |
| **Language** | TypeScript | Type safety and better DX |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **UI Components** | shadcn/ui | Accessible component library |
| **Data Fetching** | React Query | Server state management |
| **AI Chat** | OpenAI ChatKit | Pre-built chat UI components |
| **Authentication** | JWT + localStorage | Token-based auth |
| **Date Utilities** | date-fns, date-fns-tz | Date formatting and timezone handling (Phase V) |
| **Icons** | lucide-react | Icon library for UI components |
| **Deployment** | Vercel | Serverless deployment platform |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Next.js Frontend                          │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐      │
│  │   Pages     │  │  Components  │  │  API Integration │      │
│  │             │  │              │  │                  │      │
│  │ /login      │  │ TaskList     │  │ fetch() + JWT    │      │
│  │ /signup     │  │ ChatWidget   │  │ React Query      │      │
│  │ /tasks      │  │ TaskForm     │  │ Error Handling   │      │
│  │ /chat       │  │ AuthGuard    │  │                  │      │
│  └─────────────┘  └──────────────┘  └──────────────────┘      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │           Authentication (JWT in localStorage)          │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/HTTPS
                              │ Authorization: Bearer <JWT>
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │ Auth Routes  │  │ Task Routes  │  │  Chat Routes     │     │
│  │ /auth/login  │  │ /tasks       │  │  /chat           │     │
│  │ /auth/signup │  │              │  │                  │     │
│  └──────────────┘  └──────────────┘  └──────────────────┘     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │         PostgreSQL (Users, Tasks, Conversations)        │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Design Principles:**
- **Stateless**: No session storage; JWT for auth
- **API-First**: Backend API consumed via fetch/React Query
- **Component-Based**: Reusable React components
- **Type-Safe**: TypeScript throughout
- **Responsive**: Mobile-first Tailwind CSS

---

## 🤖 Frontend Agents

These FTE (Full-Time Equivalent) AI Agents specialize in frontend development tasks:

### 1. Frontend Developer (`/frontend-developer`)
**Primary Agent for Frontend Work**

**Skills Available (3):**
- `/sp.vercel-deployer` - Deploy Next.js apps to Vercel
- `/sp.ab-testing` - A/B testing framework
- `/sp.uiux-designer` - UI/UX design patterns

**Use for:**
- React component development
- Next.js page implementation
- TypeScript integration
- Tailwind CSS styling
- API integration with backend
- Responsive design
- Performance optimization

---

### 2. UI/UX Designer (`/uiux-designer`)
**Design & User Experience Specialist**

**Skills Available (2):**
- `/sp.frontend-developer` - Implement UI designs
- `/sp.ab-testing` - Test design variations

**Use for:**
- User interface design
- Design system creation
- Component library design
- Accessibility (WCAG compliance)
- User flow design
- Wireframing
- Visual hierarchy

---

### 3. Vercel Deployer (`/vercel-deployer`)
**Vercel Platform Specialist**

**Skills Available (4):**
- `/sp.deployment-automation` - Automated deployments
- `/sp.production-checklist` - Production validation
- `/sp.frontend-developer` - Next.js optimization
- `/sp.performance-logger` - Performance monitoring

**Use for:**
- Vercel deployment configuration
- Next.js optimization (ISR, SSR, SSG)
- Edge Functions
- Performance optimization
- Core Web Vitals
- CDN caching

---

### 4. QA Engineer (`/qa-engineer`)
**Frontend Testing Specialist**

**Skills Available (3):**
- `/sp.edge-case-tester` - UI edge case testing
- `/sp.ab-testing` - A/B testing framework
- `/sp.production-checklist` - Production validation

**Use for:**
- Component testing (Jest, React Testing Library)
- E2E testing (Playwright, Cypress)
- Accessibility testing
- Performance testing
- Cross-browser testing

---

## 📁 Project Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── page.tsx              # Home page (redirects to /tasks or /login)
│   ├── layout.tsx            # Root layout with providers
│   ├── login/                # Login page
│   │   └── page.tsx
│   ├── signup/               # Signup page
│   │   └── page.tsx
│   ├── tasks/                # Tasks page (protected)
│   │   └── page.tsx
│   └── chat/                 # AI Chat page (protected)
│       └── page.tsx
├── components/               # React components
│   ├── ui/                   # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   └── ... (more UI primitives)
│   ├── TaskList.tsx          # Task list component
│   ├── TaskForm.tsx          # Task creation form
│   ├── ChatWidget.tsx        # AI chat interface (OpenAI ChatKit)
│   ├── AuthGuard.tsx         # Protected route wrapper
│   ├── NavBar.tsx            # Navigation bar
│   ├── SearchInput.tsx       # Search input with debouncing (300ms)
│   ├── FilterBar.tsx         # Multi-criteria filter controls
│   ├── SearchResultsSummary.tsx  # Result count and filter summary
│   ├── Pagination.tsx        # Page navigation controls
│   ├── HighlightedText.tsx   # Keyword highlighting in results
│   └── EmptyState.tsx        # Friendly "no results" message
├── lib/                      # Utilities and helpers
│   ├── api.ts                # API client functions
│   ├── auth.ts               # Auth utilities (JWT handling)
│   └── utils.ts              # General utilities
├── hooks/                    # Custom React hooks
│   ├── useAuth.ts            # Authentication hook
│   ├── useTasks.ts           # Tasks data fetching hook
│   ├── useChat.ts            # Chat conversation hook
│   ├── useSearch.ts          # Search and filter state management
│   └── useDebounce.ts        # Debounce hook (300ms delay)
├── styles/                   # Global styles
│   └── globals.css           # Tailwind CSS imports
├── public/                   # Static assets
│   ├── favicon.ico
│   └── images/
├── .env.example              # Environment variables template
├── .env.local                # Local environment variables (gitignored)
├── next.config.js            # Next.js configuration
├── tailwind.config.ts        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
├── package.json              # Dependencies
└── README.md                 # This file
```

---

## 🚀 Setup & Installation

### Prerequisites

- **Node.js**: 18+ (LTS recommended)
- **npm**: 9+ or **yarn**: 1.22+
- **Backend**: FastAPI backend running at `http://localhost:8000`

### Installation Steps

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 2a. Install Phase V dependencies (if not already in package.json)
npm install date-fns date-fns-tz lucide-react

# 3. Create environment file
cp .env.example .env.local

# 4. Edit .env.local with your values
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 5. Start development server
npm run dev

# 6. Open browser
# Visit http://localhost:3000
```

### Environment Variables

Create `.env.local` file:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# App URL (for production)
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**⚠️ Note**: All variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

---

## 🧩 Components

### Core Components

#### 1. **TaskList** (`components/TaskList.tsx`)
Displays user's tasks with actions (complete, delete, edit).

**Props:**
```typescript
interface TaskListProps {
  tasks: Task[]
  onComplete: (taskId: string) => void
  onDelete: (taskId: string) => void
  onEdit: (taskId: string) => void
}
```

#### 2. **TaskForm** (`components/TaskForm.tsx`)
Form for creating/editing tasks.

**Props:**
```typescript
interface TaskFormProps {
  onSubmit: (task: CreateTaskDTO) => void
  initialValues?: Task
  isEditing?: boolean
}
```

#### 3. **ChatWidget** (`components/ChatWidget.tsx`)
AI chatbot interface using OpenAI ChatKit.

**Props:**
```typescript
interface ChatWidgetProps {
  conversationId?: string
  onMessage: (message: string) => void
}
```

#### 4. **AuthGuard** (`components/AuthGuard.tsx`)
HOC to protect routes requiring authentication.

**Usage:**
```typescript
export default function TasksPage() {
  return (
    <AuthGuard>
      <TaskList />
    </AuthGuard>
  )
}
```

### UI Components (shadcn/ui)

All UI primitives are in `components/ui/`:
- `Button` - Accessible button with variants
- `Input` - Form input with validation
- `Card` - Content container
- `Dialog` - Modal dialogs
- `Toast` - Notifications
- `Dropdown` - Dropdown menus
- `Badge` - Status badges and labels
- More components as needed

### Task Search Components (Feature 004-search-filter)

#### 5. **SearchInput** (`components/SearchInput.tsx`)
Search input with debouncing for optimal performance.

**Features:**
- 300ms debounce delay (configurable)
- Clear button when input has value
- Loading indicator
- Keyboard shortcuts (Cmd/Ctrl+K to focus, Escape to clear)
- Accessible (ARIA labels)

**Props:**
```typescript
interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  debounceDelay?: number  // Default: 300ms
  isLoading?: boolean
  autoFocus?: boolean
}
```

**Usage:**
```typescript
import { SearchInput } from "@/components/SearchInput"
import { useSearch } from "@/hooks/useSearch"

export function TaskSearchPage() {
  const { filters, setKeyword, isLoading } = useSearch({ userId: "user-123" })

  return (
    <SearchInput
      value={filters.keyword || ""}
      onChange={setKeyword}
      isLoading={isLoading}
      placeholder="Search tasks..."
      autoFocus
    />
  )
}
```

#### 6. **FilterBar** (`components/FilterBar.tsx`)
Multi-criteria filter controls with active filter indicators.

**Features:**
- Status filter (all/completed/incomplete)
- Priority filter (all/high/medium/low)
- Tags multi-select (OR logic)
- Due date filter (overdue/today/this week/this month/no due date)
- Clear all filters button
- Active filters summary display

**Props:**
```typescript
interface FilterBarProps {
  statusFilter: "all" | "completed" | "incomplete"
  onStatusChange: (status: "all" | "completed" | "incomplete") => void
  priorityFilter?: "all" | "high" | "medium" | "low"
  onPriorityChange?: (priority: "all" | "high" | "medium" | "low") => void
  tagsFilter?: string[]
  onTagsChange?: (tags: string[] | undefined) => void
  dueDateFilter?: "all" | "overdue" | "today" | "this_week" | "this_month" | "no_due_date"
  onDueDateChange?: (filter: ...) => void
  onClearFilters?: () => void
  hasActiveFilters?: boolean
  availableTags?: string[]
}
```

**Usage:**
```typescript
<FilterBar
  statusFilter={filters.statusFilter}
  onStatusChange={setStatusFilter}
  priorityFilter={filters.priorityFilter}
  onPriorityChange={setPriorityFilter}
  tagsFilter={filters.tagsFilter}
  onTagsChange={setTagsFilter}
  dueDateFilter={filters.dueDateFilter}
  onDueDateChange={setDueDateFilter}
  onClearFilters={resetFilters}
  hasActiveFilters={hasFilters}
  availableTags={["work", "personal", "urgent"]}
/>
```

#### 7. **SearchResultsSummary** (`components/SearchResultsSummary.tsx`)
Displays search results count with human-readable filter summary.

**Props:**
```typescript
interface SearchResultsSummaryProps {
  summary: string           // From backend: "Showing 5 incomplete high priority tasks"
  totalCount: number
  loading?: boolean
}
```

**Usage:**
```typescript
{results && (
  <SearchResultsSummary
    summary={results.appliedFilters.summary}
    totalCount={results.totalCount}
    loading={isLoading}
  />
)}
```

#### 8. **Pagination** (`components/Pagination.tsx`)
Page navigation controls with page size selection.

**Props:**
```typescript
interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  pageSize?: number
  onPageSizeChange?: (size: number) => void
  pageSizes?: number[]      // Default: [10, 20, 50, 100]
  showPageSize?: boolean
}
```

**Usage:**
```typescript
<Pagination
  currentPage={results.pagination.page}
  totalPages={results.pagination.totalPages}
  onPageChange={setPage}
  pageSize={filters.pageSize}
  onPageSizeChange={setPageSize}
/>
```

#### 9. **HighlightedText** (`components/HighlightedText.tsx`)
Highlights search keywords within text for better visual feedback.

**Props:**
```typescript
interface HighlightedTextProps {
  text: string
  keyword?: string | null
  highlightClassName?: string  // Default: "bg-yellow-200 font-medium"
}
```

**Usage:**
```typescript
<h3>
  <HighlightedText
    text={task.title}
    keyword={searchKeyword}
  />
</h3>
```

#### 10. **EmptyState** (`components/EmptyState.tsx`)
Friendly empty state message when no search results found.

**Props:**
```typescript
interface EmptyStateProps {
  message?: string         // Default: "No tasks found matching your criteria"
  suggestions?: string[]
  action?: { label: string; onClick: () => void }
}
```

**Specialized variants:**
- `NoSearchResultsState` - For search with no results
- `EmptyTasksState` - For new users with no tasks

**Usage:**
```typescript
{results.totalCount === 0 ? (
  <NoSearchResultsState onClearFilters={resetFilters} />
) : (
  <TaskList tasks={results.tasks} />
)}
```

### Custom Hooks

#### `useSearch` (`hooks/useSearch.ts`)
Manages search state and API integration with debouncing.

**Features:**
- Auto-search when filters change
- Keyword debouncing (300ms)
- Pagination support
- Loading and error states
- Filter reset functionality

**Usage:**
```typescript
import { useSearch } from "@/hooks/useSearch"

export function TaskSearchPage() {
  const {
    filters,               // Current search filters
    setKeyword,            // Update keyword filter
    setStatusFilter,       // Update status filter
    setPriorityFilter,     // Update priority filter
    setTagsFilter,         // Update tags filter
    setDueDateFilter,      // Update due date filter
    setPage,               // Change page number
    setPageSize,           // Change page size
    resetFilters,          // Clear all filters
    results,               // Search results
    isLoading,             // Loading state
    error,                 // Error state
    searchTasks,           // Manually trigger search
    hasFilters             // Whether any filters are active
  } = useSearch({ userId: "user-123" })

  return (
    <div>
      <SearchInput value={filters.keyword || ""} onChange={setKeyword} />
      <FilterBar ... />
      {results && <TaskList tasks={results.tasks} />}
    </div>
  )
}
```

#### `useDebounce` (`hooks/useDebounce.ts`)
Generic debounce hook for delaying updates.

**Usage:**
```typescript
const [searchTerm, setSearchTerm] = useState("")
const debouncedSearchTerm = useDebounce(searchTerm, 300)

useEffect(() => {
  // This runs 300ms after user stops typing
  fetchResults(debouncedSearchTerm)
}, [debouncedSearchTerm])
```

---

## 🔢 Task Sorting Components (Phase V - Feature 005-task-sort)

### Overview

The task sorting system enables users to sort their task list by multiple criteria (due date, priority, created date, title) with ascending/descending direction. Sort preferences persist during the session via sessionStorage.

**Key Features:**
- **Sort by Due Date** - Earliest first or latest first (tasks without due dates appear at end)
- **Sort by Priority** - High to low or low to high
- **Sort by Created Date** - Newest first or oldest first (default)
- **Sort Alphabetically** - A-Z or Z-A (case-insensitive)
- **Session Persistence** - Sort preferences survive page refresh
- **Visual Indicators** - Active sort field and direction (↑/↓ arrows)
- **Natural Language** - AI chatbot understands "sort by priority", "show earliest first"
- **Combined with Filters** - Sort works with search and filter results

---

### **TaskSort** Component (`components/TaskSort.tsx`)

Sort dropdown component with visual indicators and direction toggle.

**Props:**
```typescript
interface TaskSortProps {
  sortBy: SortField                 // Current sort field
  sortDirection: SortDirection       // Current sort direction
  onSortChange: (sortBy: SortField, sortDirection: SortDirection) => void
  className?: string                 // Additional Tailwind classes
}

type SortField = "due_date" | "priority" | "created_at" | "title"
type SortDirection = "asc" | "desc"
```

**Features:**
- **Dropdown menu** - Select sort field (created date, due date, priority, title)
- **Direction toggle button** - Click to reverse sort (↑/↓ icon)
- **Field-specific defaults** - Each field has sensible default direction
- **Active indicators** - Highlighted dropdown + direction arrow
- **Accessibility** - ARIA labels, keyboard navigation
- **Responsive design** - Works on mobile and desktop

**Implementation:**
```typescript
import React from "react"

export type SortField = "due_date" | "priority" | "created_at" | "title"
export type SortDirection = "asc" | "desc"

interface TaskSortProps {
  sortBy: SortField
  sortDirection: SortDirection
  onSortChange: (sortBy: SortField, sortDirection: SortDirection) => void
  className?: string
}

export default function TaskSort({
  sortBy,
  sortDirection,
  onSortChange,
  className = "",
}: TaskSortProps) {
  // Handle sort field change from dropdown
  const handleSortFieldChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSortBy = e.target.value as SortField

    // Use field-specific default direction
    const defaultDirections: Record<SortField, SortDirection> = {
      created_at: "desc",  // Newest first
      due_date: "asc",     // Earliest first
      priority: "asc",     // High → medium → low
      title: "asc"         // A → Z
    }

    const newDirection = defaultDirections[newSortBy]
    onSortChange(newSortBy, newDirection)
  }

  // Toggle sort direction (asc ↔ desc)
  const handleDirectionToggle = () => {
    const newDirection = sortDirection === "asc" ? "desc" : "asc"
    onSortChange(sortBy, newDirection)
  }

  // Get direction icon (↑ or ↓)
  const getDirectionIcon = (): string => {
    return sortDirection === "asc" ? "↑" : "↓"
  }

  // Get direction label for accessibility
  const getDirectionLabel = (): string => {
    if (sortBy === "due_date") {
      return sortDirection === "asc" ? "Earliest first" : "Latest first"
    } else if (sortBy === "priority") {
      return sortDirection === "asc" ? "High to low" : "Low to high"
    } else if (sortBy === "created_at") {
      return sortDirection === "asc" ? "Oldest first" : "Newest first"
    } else if (sortBy === "title") {
      return sortDirection === "asc" ? "A to Z" : "Z to A"
    }
    return sortDirection === "asc" ? "Ascending" : "Descending"
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Sort By Label */}
      <label
        htmlFor="task-sort-select"
        className="text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        Sort by:
      </label>

      {/* Sort Field Dropdown */}
      <select
        id="task-sort-select"
        value={sortBy}
        onChange={handleSortFieldChange}
        className="
          appearance-none rounded-md border border-gray-300
          dark:border-gray-600 bg-white dark:bg-gray-800
          px-3 py-2 pr-10 text-sm
          shadow-sm focus:border-blue-500 focus:ring-2
          focus:ring-blue-500 cursor-pointer
          hover:bg-gray-50 dark:hover:bg-gray-700
          transition-colors
        "
        aria-label="Sort tasks by"
      >
        <option value="created_at">Created Date</option>
        <option value="due_date">Due Date</option>
        <option value="priority">Priority</option>
        <option value="title">Title</option>
      </select>

      {/* Direction Toggle Button */}
      <button
        type="button"
        onClick={handleDirectionToggle}
        className="
          flex items-center gap-1 rounded-md border
          border-gray-300 dark:border-gray-600
          bg-white dark:bg-gray-800 px-3 py-2 text-sm
          shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700
          focus:outline-none focus:ring-2 focus:ring-blue-500
          transition-colors cursor-pointer
        "
        aria-label={`Sort direction: ${getDirectionLabel()}`}
        title={getDirectionLabel()}
      >
        <span className="text-lg font-bold" aria-hidden="true">
          {getDirectionIcon()}
        </span>
        <span className="sr-only">{getDirectionLabel()}</span>
      </button>
    </div>
  )
}
```

**Usage:**
```typescript
import TaskSort from "@/components/TaskSort"
import { useTaskSort } from "@/hooks/useTaskSort"

export function TaskList() {
  const { sortBy, sortDirection, handleSortChange } = useTaskSort()

  return (
    <div>
      <TaskSort
        sortBy={sortBy}
        sortDirection={sortDirection}
        onSortChange={handleSortChange}
      />

      {/* Task list with sorted tasks */}
      <ul>
        {sortedTasks.map(task => (
          <li key={task.id}>{task.title}</li>
        ))}
      </ul>
    </div>
  )
}
```

---

### **useTaskSort** Hook (`hooks/useTaskSort.ts`)

Custom React hook for managing task sorting state with session persistence.

**Interface:**
```typescript
export interface UseTaskSortReturn {
  sortBy: SortField                  // Current sort field
  sortDirection: SortDirection        // Current sort direction
  handleSortChange: (sortBy: SortField, sortDirection: SortDirection) => void
  resetSort: () => void               // Reset to default (created_at desc)
}

export type SortField = "due_date" | "priority" | "created_at" | "title"
export type SortDirection = "asc" | "desc"
```

**Features:**
- **Session persistence** - Saves preferences in sessionStorage (survives page refresh)
- **SSR compatibility** - Handles Next.js server-side rendering
- **Type safety** - TypeScript types for sort field and direction
- **Validation** - Ensures only valid sort fields and directions
- **Default sort** - created_at desc (newest first)
- **Reset function** - Clear preferences and return to default

**Implementation:**
```typescript
"use client"

import { useState, useEffect, useCallback } from "react"

export type SortField = "due_date" | "priority" | "created_at" | "title"
export type SortDirection = "asc" | "desc"

const STORAGE_KEYS = {
  SORT_BY: "task_sort_by",
  SORT_DIRECTION: "task_sort_direction",
} as const

const DEFAULT_SORT = {
  sortBy: "created_at" as SortField,
  sortDirection: "desc" as SortDirection,  // Newest first
}

export interface UseTaskSortReturn {
  sortBy: SortField
  sortDirection: SortDirection
  handleSortChange: (sortBy: SortField, sortDirection: SortDirection) => void
  resetSort: () => void
}

export function useTaskSort(): UseTaskSortReturn {
  // Initialize state from sessionStorage or defaults
  const [sortBy, setSortBy] = useState<SortField>(() => {
    if (typeof window === "undefined") return DEFAULT_SORT.sortBy

    try {
      const stored = sessionStorage.getItem(STORAGE_KEYS.SORT_BY)
      if (stored && isValidSortField(stored)) {
        return stored as SortField
      }
    } catch (error) {
      console.error("Failed to read sort preferences:", error)
    }

    return DEFAULT_SORT.sortBy
  })

  const [sortDirection, setSortDirection] = useState<SortDirection>(() => {
    if (typeof window === "undefined") return DEFAULT_SORT.sortDirection

    try {
      const stored = sessionStorage.getItem(STORAGE_KEYS.SORT_DIRECTION)
      if (stored && isValidSortDirection(stored)) {
        return stored as SortDirection
      }
    } catch (error) {
      console.error("Failed to read sort preferences:", error)
    }

    return DEFAULT_SORT.sortDirection
  })

  // Persist to sessionStorage whenever state changes
  useEffect(() => {
    if (typeof window === "undefined") return

    try {
      sessionStorage.setItem(STORAGE_KEYS.SORT_BY, sortBy)
      sessionStorage.setItem(STORAGE_KEYS.SORT_DIRECTION, sortDirection)
    } catch (error) {
      console.error("Failed to save sort preferences:", error)
    }
  }, [sortBy, sortDirection])

  // Handle sort change
  const handleSortChange = useCallback(
    (newSortBy: SortField, newSortDirection: SortDirection) => {
      setSortBy(newSortBy)
      setSortDirection(newSortDirection)
    },
    []
  )

  // Reset to default
  const resetSort = useCallback(() => {
    setSortBy(DEFAULT_SORT.sortBy)
    setSortDirection(DEFAULT_SORT.sortDirection)
  }, [])

  return {
    sortBy,
    sortDirection,
    handleSortChange,
    resetSort,
  }
}

// Type guards
function isValidSortField(value: string): boolean {
  const validFields: SortField[] = ["due_date", "priority", "created_at", "title"]
  return validFields.includes(value as SortField)
}

function isValidSortDirection(value: string): boolean {
  const validDirections: SortDirection[] = ["asc", "desc"]
  return validDirections.includes(value as SortDirection)
}
```

**Usage:**
```typescript
import { useTaskSort } from "@/hooks/useTaskSort"

function TasksPage() {
  const {
    sortBy,
    sortDirection,
    handleSortChange,
    resetSort
  } = useTaskSort()

  return (
    <div>
      <TaskSort
        sortBy={sortBy}
        sortDirection={sortDirection}
        onSortChange={handleSortChange}
      />

      <button onClick={resetSort}>Reset Sort</button>
    </div>
  )
}
```

---

### Sort Field Defaults

Each sort field has a sensible default direction that matches user expectations:

| Sort Field | Default Direction | Rationale |
|------------|-------------------|-----------|
| **created_at** | desc (newest first) | Users want to see latest tasks first |
| **due_date** | asc (earliest first) | Users want to see urgent tasks first |
| **priority** | asc (high → low) | High priority tasks should appear first |
| **title** | asc (A → Z) | Alphabetical order is standard |

**Direction Meanings:**

| Sort Field | asc (↑) | desc (↓) |
|------------|---------|----------|
| **due_date** | Earliest first | Latest first |
| **priority** | High → medium → low | Low → medium → high |
| **created_at** | Oldest first | Newest first |
| **title** | A → Z | Z → A |

---

### Session Persistence Behavior

**Storage Mechanism:**
- Uses `sessionStorage` (not `localStorage`)
- Cleared when browser tab closes
- NOT shared across tabs
- NOT synced to database (per spec)
- Survives page refresh within same tab

**Example Flow:**
```text
User opens app
  ↓
Default: created_at desc (newest first)
  ↓
User changes to: priority asc (high to low)
  ↓
sessionStorage saves: { sort_by: "priority", sort_direction: "asc" }
  ↓
User refreshes page
  ↓
Hook reads sessionStorage
  ↓
Restores: priority asc ✅
  ↓
User closes tab
  ↓
sessionStorage cleared ❌
  ↓
User reopens app
  ↓
Default again: created_at desc
```

---

### Integration with API

**Backend API Parameters:**
```typescript
// API call with sort parameters
const fetchTasks = async (sortBy: SortField, sortDirection: SortDirection) => {
  const response = await fetch(
    `${API_URL}/api/tasks?sort_by=${sortBy}&sort_direction=${sortDirection}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )
  return response.json()
}
```

**Combined with Search/Filter:**
```typescript
// Sort + search + filter
const fetchTasks = async (filters: FilterParams, sort: SortParams) => {
  const params = new URLSearchParams({
    keyword: filters.keyword || "",
    status: filters.statusFilter,
    priority: filters.priorityFilter || "all",
    sort_by: sort.sortBy,
    sort_direction: sort.sortDirection,
  })

  const response = await fetch(`${API_URL}/api/tasks?${params}`)
  return response.json()
}
```

---

### Natural Language Support

The AI chatbot understands natural language sort commands:

**User Commands:**
```text
User: "sort my tasks by due date"
→ Agent calls: list_tasks(sort_by="due_date", sort_direction="asc")

User: "show high priority first"
→ Agent calls: list_tasks(sort_by="priority", sort_direction="asc")

User: "sort alphabetically"
→ Agent calls: list_tasks(sort_by="title", sort_direction="asc")

User: "show newest first"
→ Agent calls: list_tasks(sort_by="created_at", sort_direction="desc")

User: "reverse the sort"
→ Agent toggles current direction

User: "search grocery and sort by priority"
→ Agent calls: search_tasks(keyword="grocery", sort_by="priority")
```

---

### Complete Integration Example

Full integration in TaskList page:

```typescript
"use client"

import { useState, useEffect } from "react"
import { useTaskSort } from "@/hooks/useTaskSort"
import { useSearch } from "@/hooks/useSearch"
import TaskSort from "@/components/TaskSort"
import TaskList from "@/components/TaskList"
import SearchInput from "@/components/SearchInput"
import FilterBar from "@/components/FilterBar"

export default function TasksPage() {
  const { user } = useAuth()

  // Sort state
  const { sortBy, sortDirection, handleSortChange } = useTaskSort()

  // Search/filter state
  const {
    filters,
    setKeyword,
    setStatusFilter,
    results,
    isLoading
  } = useSearch({ userId: user.id })

  // Fetch tasks when sort changes
  useEffect(() => {
    if (user) {
      fetchTasks({
        ...filters,
        sort_by: sortBy,
        sort_direction: sortDirection
      })
    }
  }, [sortBy, sortDirection, filters, user])

  return (
    <div className="container mx-auto p-4">
      {/* Search input */}
      <SearchInput
        value={filters.keyword || ""}
        onChange={setKeyword}
        isLoading={isLoading}
      />

      {/* Filter bar */}
      <FilterBar
        statusFilter={filters.statusFilter}
        onStatusChange={setStatusFilter}
      />

      {/* Sort controls */}
      <TaskSort
        sortBy={sortBy}
        sortDirection={sortDirection}
        onSortChange={handleSortChange}
        className="my-4"
      />

      {/* Task list */}
      {isLoading ? (
        <LoadingSkeleton />
      ) : results && results.tasks.length > 0 ? (
        <TaskList tasks={results.tasks} />
      ) : (
        <EmptyState message="No tasks found" />
      )}
    </div>
  )
}
```

---

### TypeScript Types

**Type Definitions:**
```typescript
// components/TaskSort.tsx and hooks/useTaskSort.ts
export type SortField = "due_date" | "priority" | "created_at" | "title"
export type SortDirection = "asc" | "desc"

export interface SortParams {
  sortBy: SortField
  sortDirection: SortDirection
}

export interface UseTaskSortReturn {
  sortBy: SortField
  sortDirection: SortDirection
  handleSortChange: (sortBy: SortField, sortDirection: SortDirection) => void
  resetSort: () => void
}
```

**API Response Types:**
```typescript
export interface Task {
  id: string
  title: string
  due_date?: string
  priority?: "high" | "medium" | "low"
  created_at: string
  // ... other fields
}

export interface TaskListResponse {
  tasks: Task[]
  totalCount: number
  pagination: {
    page: number
    pageSize: number
    totalPages: number
  }
  appliedFilters: {
    sort_by: SortField
    sort_direction: SortDirection
    // ... other filters
  }
}
```

---

### Performance Considerations

**Frontend:**
- ✅ No client-side sorting (server-side only)
- ✅ Sort state memoized with useCallback
- ✅ Session persistence (minimal overhead)
- ✅ No re-renders on non-sort state changes

**Backend:**
- ✅ Database-level ORDER BY (fast)
- ✅ Composite indexes for optimal performance
- ✅ < 200ms response for 1,000 tasks
- ✅ < 500ms response for 10,000 tasks

---

### Accessibility

**ARIA Labels:**
- Sort dropdown has descriptive label
- Direction button announces current direction
- Screen reader announces active sort

**Keyboard Navigation:**
- Tab to focus dropdown
- Arrow keys to navigate options
- Enter to select
- Tab to direction button
- Space/Enter to toggle direction

**Visual Indicators:**
- Active sort field highlighted
- Direction arrow (↑/↓) shows current direction
- Hover states for interactive elements
- Focus rings for keyboard users

---

### Resources

- **Component File:** `frontend/src/components/TaskSort.tsx`
- **Hook File:** `frontend/src/hooks/useTaskSort.ts`
- **Backend API:** See `backend/README.md` Task Sorting section
- **Specification:** `specs/005-task-sort/spec.md`
- **Tasks Breakdown:** `specs/005-task-sort/tasks.md`

---

## ⏰ Due Date Badge Components (Phase V)

### Overview

The due date badge system provides visual indicators for task due dates with color-coded urgency, reminder indicators, and timezone-aware display.

### **DueDateBadge** (`components/DueDateBadge.tsx`)

Main component for displaying due dates with visual status indicators.

**Props:**
```typescript
interface DueDateBadgeProps {
  dueDate: string | Date  // ISO string or Date object
  completed: boolean      // Task completion status
  reminders?: string[]    // Array of reminder intervals ['24h', '1h']
  className?: string      // Additional Tailwind classes
}
```

**Implementation:**
```typescript
import { format, isToday, isTomorrow, isPast, differenceInHours } from 'date-fns'
import { toZonedTime } from 'date-fns-tz'
import { Badge } from '@/components/ui/badge'
import { Clock, Bell } from 'lucide-react'

export const DueDateBadge = ({
  dueDate,
  completed,
  reminders = [],
  className
}: DueDateBadgeProps) => {
  // Convert to user's local timezone
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
  const zonedDate = toZonedTime(new Date(dueDate), userTimezone)

  // Calculate status
  const isOverdue = isPast(zonedDate) && !completed
  const isDueToday = isToday(zonedDate)
  const isDueTomorrow = isTomorrow(zonedDate)
  const hoursUntilDue = differenceInHours(zonedDate, new Date())

  // Determine badge variant
  let variant: 'default' | 'destructive' | 'warning' | 'success' = 'default'
  if (completed) {
    variant = 'success'
  } else if (isOverdue) {
    variant = 'destructive'
  } else if (isDueToday || hoursUntilDue <= 24) {
    variant = 'warning'
  }

  // Format date
  let dateText: string
  if (isDueToday) {
    dateText = `Today at ${format(zonedDate, 'h:mm a')}`
  } else if (isDueTomorrow) {
    dateText = `Tomorrow at ${format(zonedDate, 'h:mm a')}`
  } else {
    dateText = format(zonedDate, 'MMM d, h:mm a')
  }

  return (
    <div className="flex items-center gap-2">
      <Badge variant={variant} className={className}>
        <Clock className="w-3 h-3 mr-1" />
        {dateText}
      </Badge>

      {reminders.length > 0 && (
        <Badge variant="outline" className="text-xs">
          <Bell className="w-3 h-3 mr-1" />
          {reminders.join(', ')}
        </Badge>
      )}
    </div>
  )
}
```

**Usage:**
```typescript
// In TaskList component
<DueDateBadge
  dueDate={task.due_date}
  completed={task.completed}
  reminders={task.remind_before}
/>

// Result examples:
// ⏰ Today at 5:00 pm        🔔 24h, 1h    (Due today - warning)
// ⏰ Tomorrow at 9:00 am      🔔 24h        (Due tomorrow - warning)
// ⏰ Feb 20, 2:30 pm          🔔 24h, 1h    (Upcoming - default)
// ⏰ Feb 10, 3:00 pm                        (Overdue - destructive)
// ⏰ Feb 15, 10:00 am                       (Completed - success)
```

### **ReminderIndicator** (`components/ReminderIndicator.tsx`)

Displays reminder status and intervals.

**Props:**
```typescript
interface ReminderIndicatorProps {
  reminders: string[]       // ['24h', '1h', 'custom']
  reminderSent: Record<string, string>  // {'24h': '2026-02-14T10:00:00Z'}
  className?: string
}
```

**Implementation:**
```typescript
import { Badge } from '@/components/ui/badge'
import { Bell, BellRing } from 'lucide-react'

export const ReminderIndicator = ({
  reminders,
  reminderSent,
  className
}: ReminderIndicatorProps) => {
  if (reminders.length === 0) return null

  return (
    <div className="flex items-center gap-1">
      {reminders.map((interval) => {
        const sent = reminderSent[interval]
        const Icon = sent ? BellRing : Bell
        const variant = sent ? 'success' : 'outline'

        return (
          <Badge
            key={interval}
            variant={variant}
            className={className}
            title={sent ? `Reminder sent at ${new Date(sent).toLocaleString()}` : 'Pending'}
          >
            <Icon className="w-3 h-3 mr-1" />
            {interval}
          </Badge>
        )
      })}
    </div>
  )
}
```

**Usage:**
```typescript
<ReminderIndicator
  reminders={['24h', '1h']}
  reminderSent={{ '24h': '2026-02-14T10:00:00Z' }}
/>

// Result:
// 🔔 24h ✓    🔔 1h
// (24h sent, 1h pending)
```

### **StatusBadge** (`components/StatusBadge.tsx`)

Shows task status with visual indicators (overdue, due soon, upcoming).

**Props:**
```typescript
interface StatusBadgeProps {
  dueDate: string | Date
  completed: boolean
  size?: 'sm' | 'md' | 'lg'
}
```

**Implementation:**
```typescript
import { differenceInHours, isPast } from 'date-fns'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, Clock, CheckCircle } from 'lucide-react'

export const StatusBadge = ({ dueDate, completed, size = 'md' }: StatusBadgeProps) => {
  const date = new Date(dueDate)
  const hoursUntilDue = differenceInHours(date, new Date())
  const isOverdue = isPast(date) && !completed

  let status: { text: string; variant: string; icon: React.ComponentType }

  if (completed) {
    status = { text: 'Completed', variant: 'success', icon: CheckCircle }
  } else if (isOverdue) {
    status = { text: 'Overdue', variant: 'destructive', icon: AlertCircle }
  } else if (hoursUntilDue <= 24) {
    status = { text: 'Due Soon', variant: 'warning', icon: Clock }
  } else {
    status = { text: 'Upcoming', variant: 'default', icon: Clock }
  }

  const Icon = status.icon

  return (
    <Badge variant={status.variant as any} className={size === 'sm' ? 'text-xs' : ''}>
      <Icon className={`${size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} mr-1`} />
      {status.text}
    </Badge>
  )
}
```

**Usage:**
```typescript
<StatusBadge
  dueDate={task.due_date}
  completed={task.completed}
  size="sm"
/>

// Result examples:
// ⚠️ Overdue
// ⏰ Due Soon
// ⏰ Upcoming
// ✓ Completed
```

---

## 🏷️ Task Tags & Categories Components (Phase V)

### Overview

The task tags system provides visual organization with color-coded badges, autocomplete input, and tag management functionality.

**Key Features:**
- **Deterministic colors** - Same tag always generates the same color
- **Tag normalization** - Automatic lowercase conversion and deduplication
- **Autocomplete** - Suggests existing tags as you type
- **Validation** - Only allows valid characters (alphanumeric, hyphens, underscores)
- **Keyboard navigation** - Full keyboard support (Enter, Backspace, Arrow keys)
- **User isolation** - Tags are scoped to authenticated user

---

### **TagBadge** (`components/TagBadge.tsx`)

Display individual tags with consistent, deterministic colors.

**Props:**
```typescript
interface TagBadgeProps {
  tag: string              // Tag name
  size?: 'sm' | 'md' | 'lg'  // Badge size
  className?: string       // Additional classes
  onClick?: () => void     // Optional click handler
}
```

**Implementation:**
```typescript
import { generateTagColor, getContrastColor } from '@/utils/tagColors'

export const TagBadge: React.FC<TagBadgeProps> = ({
  tag,
  size = 'md',
  className = '',
  onClick
}) => {
  const backgroundColor = generateTagColor(tag)
  const textColor = getContrastColor(backgroundColor)

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5'
  }

  return (
    <span
      style={{ backgroundColor, color: textColor }}
      className={`inline-flex items-center rounded-full font-medium ${sizeClasses[size]} ${className}`}
      onClick={onClick}
    >
      {tag}
    </span>
  )
}
```

**TagList Component:**
```typescript
export const TagList: React.FC<TagListProps> = ({
  tags,
  size = 'md',
  onTagClick
}) => {
  if (tags.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag) => (
        <TagBadge
          key={tag}
          tag={tag}
          size={size}
          onClick={() => onTagClick?.(tag)}
        />
      ))}
    </div>
  )
}
```

**Usage:**
```typescript
// Single tag
<TagBadge tag="work" size="md" />
<TagBadge tag="urgent" size="sm" />

// Tag list
<TagList tags={['work', 'urgent', 'important']} size="md" />

// In TaskCard
<div className="mt-2">
  {task.tags && task.tags.length > 0 && (
    <TagList tags={task.tags} size="sm" />
  )}
</div>
```

---

### **TagInput** (`components/TagInput.tsx`)

Interactive input for adding and managing tags with autocomplete.

**Props:**
```typescript
interface TagInputProps {
  tags: string[]                    // Current tags
  onChange: (tags: string[]) => void  // Update handler
  suggestions?: string[]            // Autocomplete suggestions
  placeholder?: string              // Input placeholder
  maxTags?: number                  // Max tags allowed (default: 100)
  size?: 'sm' | 'md' | 'lg'        // Input size
  className?: string                // Additional classes
  disabled?: boolean                // Disabled state
}
```

**Features:**
- **Autocomplete dropdown** with keyboard navigation
- **Enter** to add tag
- **Backspace** on empty input to remove last tag
- **Arrow keys** to navigate suggestions
- **Escape** to close suggestions
- **Click outside** to close suggestions
- **Validation** - max 50 chars, alphanumeric + hyphens + underscores
- **Deduplication** - case-insensitive duplicate detection

**Implementation:**
```typescript
import { TagBadge } from './TagBadge'
import { X } from 'lucide-react'

export const TagInput: React.FC<TagInputProps> = ({
  tags,
  onChange,
  suggestions = [],
  placeholder = 'Add tags...',
  maxTags = 100,
  size = 'md',
  disabled = false
}) => {
  const [inputValue, setInputValue] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)

  const addTag = (tag: string) => {
    const normalized = tag.toLowerCase().trim()

    // Validation
    if (!normalized) return
    if (normalized.length > 50) return
    if (tags.map(t => t.toLowerCase()).includes(normalized)) return
    if (tags.length >= maxTags) return
    if (!/^[a-z0-9_-]+$/.test(normalized)) return

    onChange([...tags, normalized])
    setInputValue('')
  }

  return (
    <div>
      {/* Display current tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {tags.map((tag, index) => (
            <div key={index} className="flex items-center gap-1">
              <TagBadge tag={tag} size={size} />
              <button onClick={() => removeTag(index)}>
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input with autocomplete */}
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || tags.length >= maxTags}
      />

      {/* Autocomplete suggestions */}
      {showSuggestions && (
        <div className="autocomplete-dropdown">
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={suggestion}
              onClick={() => addTag(suggestion)}
              className={index === selectedIndex ? 'selected' : ''}
            >
              <TagBadge tag={suggestion} size="sm" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

**Usage:**
```typescript
import { TagInput } from '@/components/TagInput'
import { useTags } from '@/hooks/useTags'

function TaskForm() {
  const { tags, setTags, availableTags } = useTags({
    initialTags: [],
    fetchAvailableTags: true
  })

  return (
    <div>
      <TagInput
        tags={tags}
        onChange={setTags}
        suggestions={availableTags}
        placeholder="Add tags (e.g., work, urgent)..."
        maxTags={10}
      />
    </div>
  )
}
```

---

### **useTags Hook** (`hooks/useTags.ts`)

React hook for tag management state and operations.

**Interface:**
```typescript
interface UseTagsReturn {
  tags: string[]                    // Current tags
  addTag: (tag: string) => boolean  // Add tag (returns success)
  removeTag: (index: number) => void  // Remove by index
  setTags: (tags: string[]) => void   // Set all tags
  clearTags: () => void               // Clear all
  hasTag: (tag: string) => boolean    // Check existence
  availableTags: string[]             // Autocomplete suggestions
  tagInfo: TagInfo[]                  // Tags with counts + colors
  isLoading: boolean                  // Fetch state
  error: string | null                // Error state
  refreshAvailableTags: () => Promise<void>  // Refetch
  validationError: string | null      // Validation error
}
```

**Usage:**
```typescript
import { useTags } from '@/hooks/useTags'

function Component() {
  const {
    tags,
    addTag,
    removeTag,
    availableTags,
    isLoading,
    validationError
  } = useTags({
    initialTags: ['work'],
    fetchAvailableTags: true,
    maxTags: 10
  })

  const handleAdd = () => {
    const success = addTag('urgent')
    if (!success) {
      console.error(validationError)
    }
  }

  return (
    <div>
      <TagInput
        tags={tags}
        onChange={setTags}
        suggestions={availableTags}
      />
      {validationError && <p className="text-red-500">{validationError}</p>}
    </div>
  )
}
```

---

### **Color Generation** (`utils/tagColors.ts`)

Deterministic color generation ensures same tag always has the same color.

**Algorithm:**
1. MD5 hash of tag name
2. Extract RGB from first 6 hex chars
3. Adjust brightness if too dark (min 128)
4. Return hex color code

**Implementation:**
```typescript
export function generateTagColor(tagName: string): string {
  const hash = md5(tagName)
  let r = parseInt(hash.substring(0, 2), 16)
  let g = parseInt(hash.substring(2, 4), 16)
  let b = parseInt(hash.substring(4, 6), 16)

  // Ensure minimum brightness
  const brightness = (r * 299 + g * 587 + b * 114) / 1000
  if (brightness < 128) {
    r = Math.min(255, r + 80)
    g = Math.min(255, g + 80)
    b = Math.min(255, b + 80)
  }

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

export function getContrastColor(backgroundColor: string): string {
  // Calculate luminance and return black or white for contrast
  const r = parseInt(backgroundColor.substring(1, 3), 16)
  const g = parseInt(backgroundColor.substring(3, 5), 16)
  const b = parseInt(backgroundColor.substring(5, 7), 16)

  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.5 ? '#000000' : '#FFFFFF'
}
```

**Consistency:**
```typescript
// Same tag always generates same color
generateTagColor('work')     // Always returns same hex (e.g., #3b82f6)
generateTagColor('work')     // Always returns same hex
generateTagColor('WORK')     // Same result (normalized to lowercase)

// Different tags get different colors
generateTagColor('work')     // #3b82f6
generateTagColor('urgent')   // #ef4444
generateTagColor('shopping') // #10b981
```

---

### **Integration Example**

Complete integration in TaskCard:

```typescript
import { TagList } from '@/components/TagBadge'
import { useTags } from '@/hooks/useTags'

export function TaskCard({ task }: { task: Task }) {
  return (
    <div className="border rounded-lg p-4">
      <h3>{task.title}</h3>
      <p>{task.description}</p>

      {/* Display tags */}
      {task.tags && task.tags.length > 0 && (
        <div className="mt-2">
          <TagList tags={task.tags} size="sm" />
        </div>
      )}

      {/* Due date badge */}
      {task.due_date && (
        <DueDateBadge dueDate={task.due_date} completed={task.completed} />
      )}
    </div>
  )
}
```

---

## 📅 date-fns Integration (Phase V)

### Overview

**date-fns** is a modern date utility library providing immutable, pure functions for date manipulation and formatting. Used throughout the frontend for consistent date handling.

### Installation

```bash
npm install date-fns date-fns-tz
```

### Core Functions Used

#### 1. **Formatting Dates** (`format`)

```typescript
import { format } from 'date-fns'

// Display formats
format(new Date('2026-02-14T15:30:00Z'), 'MMM d, yyyy')
// → "Feb 14, 2026"

format(new Date('2026-02-14T15:30:00Z'), 'h:mm a')
// → "3:30 PM"

format(new Date('2026-02-14T15:30:00Z'), 'MMM d, h:mm a')
// → "Feb 14, 3:30 PM"

format(new Date('2026-02-14T15:30:00Z'), 'EEEE, MMMM do, yyyy')
// → "Friday, February 14th, 2026"
```

#### 2. **Relative Time** (`isToday`, `isTomorrow`, `isPast`)

```typescript
import { isToday, isTomorrow, isPast, isFuture } from 'date-fns'

const dueDate = new Date('2026-02-15T09:00:00Z')

isToday(dueDate)      // → true if today
isTomorrow(dueDate)   // → true if tomorrow
isPast(dueDate)       // → true if before now
isFuture(dueDate)     // → true if after now
```

#### 3. **Date Differences** (`differenceInHours`, `differenceInDays`)

```typescript
import { differenceInHours, differenceInDays, differenceInMinutes } from 'date-fns'

const dueDate = new Date('2026-02-15T09:00:00Z')
const now = new Date()

differenceInHours(dueDate, now)
// → 24 (hours until due)

differenceInDays(dueDate, now)
// → 1 (days until due)

differenceInMinutes(dueDate, now)
// → 1440 (minutes until due)
```

#### 4. **Timezone Conversion** (`date-fns-tz`)

```typescript
import { toZonedTime, format } from 'date-fns-tz'

// Convert UTC to user's timezone
const utcDate = new Date('2026-02-14T15:30:00Z')
const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone  // 'America/New_York'

const zonedDate = toZonedTime(utcDate, userTimezone)

format(zonedDate, 'MMM d, h:mm a zzz', { timeZone: userTimezone })
// → "Feb 14, 10:30 AM EST"
```

#### 5. **Date Manipulation** (`add`, `sub`)

```typescript
import { add, sub } from 'date-fns'

const now = new Date()

// Add time
add(now, { days: 1 })       // Tomorrow
add(now, { hours: 24 })     // 24 hours from now
add(now, { weeks: 1 })      // 1 week from now

// Subtract time
sub(now, { days: 1 })       // Yesterday
sub(now, { hours: 1 })      // 1 hour ago
```

### Utility Functions (`lib/dateUtils.ts`)

Create a central date utilities file:

```typescript
// lib/dateUtils.ts
import {
  format,
  isToday,
  isTomorrow,
  isPast,
  differenceInHours,
  differenceInDays
} from 'date-fns'
import { toZonedTime } from 'date-fns-tz'

/**
 * Format due date with relative text
 * Examples: "Today at 5pm", "Tomorrow at 9am", "Feb 14 at 2:30pm"
 */
export const formatDueDate = (dueDate: string | Date): string => {
  const userTimezone = getUserTimezone()
  const zonedDate = toZonedTime(new Date(dueDate), userTimezone)

  if (isToday(zonedDate)) {
    return `Today at ${format(zonedDate, 'h:mm a')}`
  }

  if (isTomorrow(zonedDate)) {
    return `Tomorrow at ${format(zonedDate, 'h:mm a')}`
  }

  return format(zonedDate, 'MMM d at h:mm a')
}

/**
 * Get time remaining text
 * Examples: "in 2 hours", "in 3 days", "overdue by 1 hour"
 */
export const getTimeRemaining = (dueDate: string | Date): string => {
  const date = new Date(dueDate)
  const now = new Date()

  if (isPast(date)) {
    const hours = Math.abs(differenceInHours(date, now))
    if (hours < 24) {
      return `overdue by ${hours} hour${hours === 1 ? '' : 's'}`
    }
    const days = Math.abs(differenceInDays(date, now))
    return `overdue by ${days} day${days === 1 ? '' : 's'}`
  }

  const hours = differenceInHours(date, now)
  if (hours < 24) {
    return `in ${hours} hour${hours === 1 ? '' : 's'}`
  }

  const days = differenceInDays(date, now)
  return `in ${days} day${days === 1 ? '' : 's'}`
}

/**
 * Get user's timezone
 */
export const getUserTimezone = (): string => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

/**
 * Convert UTC date to user's local timezone
 */
export const toUserTimezone = (utcDate: string | Date): Date => {
  const userTz = getUserTimezone()
  return toZonedTime(new Date(utcDate), userTz)
}

/**
 * Check if task is due soon (within 24 hours)
 */
export const isDueSoon = (dueDate: string | Date): boolean => {
  const hours = differenceInHours(new Date(dueDate), new Date())
  return hours > 0 && hours <= 24
}

/**
 * Check if task is overdue
 */
export const isOverdue = (dueDate: string | Date, completed: boolean): boolean => {
  return isPast(new Date(dueDate)) && !completed
}
```

### Usage in Components

```typescript
// components/TaskList.tsx
import { formatDueDate, getTimeRemaining, isDueSoon, isOverdue } from '@/lib/dateUtils'

export const TaskList = ({ tasks }: TaskListProps) => {
  return (
    <ul>
      {tasks.map((task) => (
        <li key={task.id}>
          <h3>{task.title}</h3>

          {/* Due date badge */}
          <DueDateBadge
            dueDate={task.due_date}
            completed={task.completed}
            reminders={task.remind_before}
          />

          {/* Time remaining */}
          <p className="text-sm text-gray-600">
            {getTimeRemaining(task.due_date)}
          </p>

          {/* Status indicators */}
          {isOverdue(task.due_date, task.completed) && (
            <Badge variant="destructive">Overdue</Badge>
          )}

          {isDueSoon(task.due_date) && !task.completed && (
            <Badge variant="warning">Due Soon</Badge>
          )}
        </li>
      ))}
    </ul>
  )
}
```

### Best Practices

**1. Always use user's timezone:**
```typescript
// ✅ CORRECT
const userTz = Intl.DateTimeFormat().resolvedOptions().timeZone
const zonedDate = toZonedTime(utcDate, userTz)

// ❌ WRONG - Assumes UTC
const date = new Date(utcDate)
```

**2. Store dates as ISO strings:**
```typescript
// ✅ CORRECT - ISO string from backend
dueDate: "2026-02-14T15:30:00Z"

// ❌ WRONG - Locale-specific string
dueDate: "2/14/2026 3:30 PM"
```

**3. Use immutable operations:**
```typescript
// ✅ CORRECT - date-fns is immutable
const tomorrow = add(today, { days: 1 })

// ❌ WRONG - Mutates original date
today.setDate(today.getDate() + 1)
```

**4. Handle timezones explicitly:**
```typescript
// ✅ CORRECT - Explicit timezone conversion
format(zonedDate, 'MMM d, h:mm a zzz', { timeZone: userTimezone })

// ❌ WRONG - Assumes browser timezone
format(date, 'MMM d, h:mm a')
```

### date-fns Format Tokens

| Token | Example | Description |
|-------|---------|-------------|
| `MM` | 02 | Month (2-digit) |
| `MMM` | Feb | Month (abbreviated) |
| `MMMM` | February | Month (full name) |
| `d` | 14 | Day of month |
| `do` | 14th | Day of month (ordinal) |
| `yyyy` | 2026 | Year (4-digit) |
| `h` | 3 | Hour (12-hour) |
| `H` | 15 | Hour (24-hour) |
| `mm` | 30 | Minutes |
| `a` | PM | AM/PM |
| `zzz` | EST | Timezone abbreviation |
| `EEEE` | Friday | Day of week (full) |
| `EEE` | Fri | Day of week (abbreviated) |

### Resources

- **date-fns Docs**: https://date-fns.org/docs/
- **date-fns-tz Docs**: https://github.com/marnusw/date-fns-tz
- **Format Tokens**: https://date-fns.org/docs/format

---

## 📄 Pages & Routes

### Public Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Redirects to `/tasks` (if authenticated) or `/login` |
| `/login` | Login | User login form |
| `/signup` | Signup | User registration form |

### Protected Routes

| Route | Page | Description |
|-------|------|-------------|
| `/tasks` | Tasks | Traditional task management UI |
| `/chat` | Chat | AI chatbot interface |

**Protected Route Logic:**
```typescript
// app/tasks/page.tsx
export default function TasksPage() {
  const router = useRouter()
  const { user, loading } = useAuth()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  if (loading) return <LoadingSkeleton />
  if (!user) return null

  return <TasksPageContent />
}
```

---

## 🔌 API Integration

### API Client (`lib/api.ts`)

**Base Configuration:**
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = {
  async fetch(endpoint: string, options?: RequestInit) {
    const token = localStorage.getItem('token')
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options?.headers,
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }

    return response
  }
}
```

### API Endpoints Used

#### Authentication
```typescript
// POST /api/auth/signup
const signup = async (data: SignupDTO) => {
  const response = await apiClient.fetch('/api/auth/signup', {
    method: 'POST',
    body: JSON.stringify(data),
  })
  return response.json()
}

// POST /api/auth/login
const login = async (data: LoginDTO) => {
  const response = await apiClient.fetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  })
  const { access_token } = await response.json()
  localStorage.setItem('token', access_token)
  return access_token
}
```

#### Tasks
```typescript
// GET /api/tasks
const getTasks = async () => {
  const response = await apiClient.fetch('/api/tasks')
  return response.json()
}

// POST /api/tasks
const createTask = async (data: CreateTaskDTO) => {
  const response = await apiClient.fetch('/api/tasks', {
    method: 'POST',
    body: JSON.stringify(data),
  })
  return response.json()
}

// PATCH /api/tasks/{task_id}
const updateTask = async (taskId: string, data: UpdateTaskDTO) => {
  const response = await apiClient.fetch(`/api/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
  return response.json()
}

// DELETE /api/tasks/{task_id}
const deleteTask = async (taskId: string) => {
  await apiClient.fetch(`/api/tasks/${taskId}`, {
    method: 'DELETE',
  })
}
```

#### Chat
```typescript
// POST /api/chat
const sendChatMessage = async (message: string, conversationId?: string) => {
  const response = await apiClient.fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, conversation_id: conversationId }),
  })
  return response.json()
}

// GET /api/conversations/{conversation_id}
const getConversation = async (conversationId: string) => {
  const response = await apiClient.fetch(`/api/conversations/${conversationId}`)
  return response.json()
}
```

### React Query Integration

```typescript
// hooks/useTasks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTasks, createTask, updateTask, deleteTask } from '@/lib/api'

export const useTasks = () => {
  const queryClient = useQueryClient()

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: getTasks,
  })

  const createMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateTask(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  return {
    tasks,
    isLoading,
    createTask: createMutation.mutate,
    updateTask: updateMutation.mutate,
    deleteTask: deleteMutation.mutate,
  }
}
```

---

## 🔐 Authentication

### JWT Token Flow

```
┌──────────┐                          ┌──────────┐
│  User    │                          │ Backend  │
└────┬─────┘                          └────┬─────┘
     │                                     │
     │  1. Login (email, password)         │
     ├────────────────────────────────────>│
     │                                     │
     │  2. JWT Token                       │
     │<────────────────────────────────────┤
     │                                     │
     │  3. Store in localStorage           │
     │                                     │
     │  4. API Request + Auth Header       │
     ├────────────────────────────────────>│
     │    Authorization: Bearer <JWT>      │
     │                                     │
     │  5. Response                        │
     │<────────────────────────────────────┤
     │                                     │
```

### Auth Hook (`hooks/useAuth.ts`)

```typescript
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      // Decode JWT to get user info (or fetch from /api/me)
      const decoded = jwtDecode(token)
      setUser(decoded.user)
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const token = await apiClient.login({ email, password })
    const decoded = jwtDecode(token)
    setUser(decoded.user)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
    router.push('/login')
  }

  return { user, loading, login, logout }
}
```

### Protected Route Pattern

```typescript
// components/AuthGuard.tsx
export const AuthGuard = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  if (loading) return <LoadingSpinner />
  if (!user) return null

  return <>{children}</>
}
```

---

## 🎨 Styling & Design

### Tailwind CSS Configuration

```javascript
// tailwind.config.ts
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
      },
    },
  },
  plugins: [],
}
```

### Design Tokens

**Colors:**
```css
/* Primary */
--primary-50: #eff6ff;
--primary-500: #3b82f6;
--primary-900: #1e3a8a;

/* Usage */
.btn-primary { @apply bg-primary-500 text-white; }
```

**Typography:**
```css
text-xs    /* 12px */
text-sm    /* 14px */
text-base  /* 16px */
text-lg    /* 18px */
text-xl    /* 20px */
text-2xl   /* 24px */
```

**Spacing:**
```css
space-1  /* 4px */
space-2  /* 8px */
space-4  /* 16px */
space-8  /* 32px */
```

### Component Variants

```typescript
// Example: Button component
<Button variant="primary">Submit</Button>
<Button variant="secondary">Cancel</Button>
<Button variant="outline">Edit</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
```

---

## 🧪 Testing

### Unit/Component Tests (Jest + React Testing Library)

```bash
# Run all tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

**Example Component Test:**
```typescript
// __tests__/TaskList.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TaskList } from '@/components/TaskList'

test('renders tasks correctly', () => {
  const tasks = [
    { id: '1', title: 'Buy milk', completed: false },
    { id: '2', title: 'Walk dog', completed: true },
  ]

  render(<TaskList tasks={tasks} onComplete={jest.fn()} onDelete={jest.fn()} />)

  expect(screen.getByText('Buy milk')).toBeInTheDocument()
  expect(screen.getByText('Walk dog')).toBeInTheDocument()
})

test('calls onComplete when checkbox clicked', async () => {
  const onComplete = jest.fn()
  const tasks = [{ id: '1', title: 'Buy milk', completed: false }]

  render(<TaskList tasks={tasks} onComplete={onComplete} onDelete={jest.fn()} />)

  const checkbox = screen.getByRole('checkbox')
  await userEvent.click(checkbox)

  expect(onComplete).toHaveBeenCalledWith('1')
})
```

### E2E Tests (Playwright)

```bash
# Run E2E tests
npm run test:e2e

# Open UI mode
npm run test:e2e:ui
```

**Example E2E Test:**
```typescript
// e2e/tasks.spec.ts
import { test, expect } from '@playwright/test'

test('user can create a task', async ({ page }) => {
  // Login
  await page.goto('/login')
  await page.fill('[name="email"]', 'test@example.com')
  await page.fill('[name="password"]', 'password123')
  await page.click('button:has-text("Login")')

  // Create task
  await page.goto('/tasks')
  await page.fill('[placeholder="Add new task"]', 'Buy groceries')
  await page.click('button:has-text("Add")')

  // Verify
  await expect(page.locator('text=Buy groceries')).toBeVisible()
})
```

### Accessibility Tests

```typescript
// __tests__/accessibility.test.tsx
import { render } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

test('TaskList has no accessibility violations', async () => {
  const { container } = render(<TaskList tasks={[]} />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

---

## 🚀 Deployment

### Vercel Deployment

#### Method 1: GitHub Integration (Recommended)

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import GitHub repository
4. Configure environment variables:
   - `NEXT_PUBLIC_API_URL=https://your-backend.com`
5. Deploy

#### Method 2: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Production deployment
vercel --prod
```

### Environment Variables (Production)

Set in Vercel Dashboard:
```
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_APP_URL=https://your-domain.com
```

### Build Configuration

```javascript
// next.config.js
module.exports = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
}
```

### Production Checklist

- [ ] Environment variables configured
- [ ] Build succeeds (`npm run build`)
- [ ] No console errors in production build
- [ ] HTTPS enabled
- [ ] CORS configured on backend
- [ ] Performance optimized (Lighthouse > 90)
- [ ] SEO metadata added
- [ ] Error tracking configured (Sentry)
- [ ] Analytics configured (Google Analytics)

---

## 📚 Resources

### Documentation
- **Root CLAUDE.md**: `../CLAUDE.md` - Project-wide guidelines
- **Backend CLAUDE.md**: `../backend/CLAUDE.md` - Backend-specific guides
- **Constitution**: `../.specify/memory/constitution.md` - Project principles
- **Skills Directory**: `../.claude/skills/` - All reusable skills
- **Agents Directory**: `../.claude/agents/` - All FTE agents

### External Docs
- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com)
- [React Query Documentation](https://tanstack.com/query/latest)
- [OpenAI ChatKit](https://platform.openai.com/docs/chatkit)

### Scripts Reference

```bash
# Development
npm run dev              # Start dev server (http://localhost:3000)

# Building
npm run build            # Production build
npm run start            # Start production server

# Testing
npm run test             # Run unit/component tests
npm run test:watch       # Watch mode
npm run test:coverage    # Coverage report
npm run test:e2e         # E2E tests (Playwright)

# Linting & Formatting
npm run lint             # ESLint
npm run lint:fix         # Fix linting issues
npm run format           # Prettier
npm run type-check       # TypeScript type checking

# Analysis
npm run analyze          # Bundle size analysis
```

---

## 🏆 Best Practices

### Component Design
- ✅ Single Responsibility Principle
- ✅ Reusable and composable
- ✅ Typed with TypeScript
- ✅ Props interface documented
- ✅ Default props defined

### State Management
- ✅ React Query for server state
- ✅ Context API for global UI state
- ✅ Local state with useState
- ✅ Avoid prop drilling
- ✅ Memoize expensive computations

### Performance
- ✅ `next/image` for images
- ✅ Dynamic imports for code splitting
- ✅ `React.memo` for expensive components
- ✅ `useCallback`/`useMemo` where needed
- ✅ Virtualization for long lists

### Accessibility
- ✅ Semantic HTML elements
- ✅ ARIA labels and roles
- ✅ Keyboard navigation support
- ✅ Focus management
- ✅ Screen reader compatibility

---

**Frontend Development** - Powered by Reusable Intelligence 🚀

**For detailed agent and skill usage, see:**
- `../CLAUDE.md` - Root documentation
- `./CLAUDE.md` - Frontend-specific guide
- `../.claude/agents/` - FTE agent definitions
- `../.claude/skills/` - Reusable intelligence skills
