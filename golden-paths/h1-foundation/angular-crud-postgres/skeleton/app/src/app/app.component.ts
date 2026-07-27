import { Component, signal } from '@angular/core';
import { Task } from './core/models/task.model';
import { TaskFormComponent } from './features/task-form/task-form.component';
import { TaskListComponent } from './features/task-list/task-list.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [TaskListComponent, TaskFormComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  editingTask = signal<Task | null>(null);
  refreshToken = signal(0);

  onEdit(task: Task): void {
    this.editingTask.set(task);
  }

  onSaved(): void {
    this.editingTask.set(null);
    this.refreshToken.update((n) => n + 1);
  }

  onCancelEdit(): void {
    this.editingTask.set(null);
  }
}
