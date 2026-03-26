export type Task = {
  id: number;
  title: string;
  description?: string | null;
  completed: boolean;
  priority: 'high' | 'medium' | 'low';
  due_date?: string | null;
  created_at?: string;
  updated_at?: string;
  // Phase V: Recurring tasks fields
  is_recurring?: boolean;
  recurrence_pattern?: string | null;
  recurrence_end_date?: string | null;
  parent_task_id?: number | null;
  // Phase V Part B: Due dates & reminders fields
  due_date_formatted?: string | null;
  is_overdue?: boolean;
  overdue_by?: string | null;
  remind_before?: string[] | null;
  reminder_sent?: Record<string, string> | null;
  // Phase V Part C: Task Tags & Categories (003-task-tags)
  tags?: string[];
};

export type AuthUser = {
  id: string;
  email: string;
  name?: string | null;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export type SignupResponse = {
  id: string;
  email: string;
  name?: string | null;
};

export type ApiError = {
  status: number;
  message: string;
  unauthorized?: boolean;
};
