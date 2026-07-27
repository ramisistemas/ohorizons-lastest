export interface Task {
  id?: number;
  title: string;
  notes: string | null;
  done: boolean;
  created_at?: string;
}

export type TaskInput = Omit<Task, 'id' | 'created_at'>;
