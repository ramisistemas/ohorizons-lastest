import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, Output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Task } from '../../core/models/task.model';
import { TaskService } from '../../core/services/task.service';

@Component({
  selector: 'app-task-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './task-form.component.html',
  styleUrl: './task-form.component.css',
})
export class TaskFormComponent implements OnChanges {
  @Input() task: Task | null = null;
  @Output() saved = new EventEmitter<void>();
  @Output() cancelled = new EventEmitter<void>();

  submitting = false;
  error: string | null = null;

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    notes: [''],
    done: [false],
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly taskService: TaskService,
  ) {}

  ngOnChanges(): void {
    if (this.task) {
      this.form.setValue({
        title: this.task.title,
        notes: this.task.notes ?? '',
        done: this.task.done,
      });
    } else {
      this.form.reset({ title: '', notes: '', done: false });
    }
  }

  get isEditing(): boolean {
    return !!this.task?.id;
  }

  submit(): void {
    if (this.form.invalid) return;

    this.submitting = true;
    this.error = null;
    const value = this.form.getRawValue();

    const request = this.isEditing
      ? this.taskService.update(this.task!.id!, value)
      : this.taskService.create(value);

    request.subscribe({
      next: () => {
        this.submitting = false;
        this.saved.emit();
      },
      error: () => {
        this.submitting = false;
        this.error = 'No se pudo guardar. Revisa la conexión con PostgREST.';
      },
    });
  }

  cancel(): void {
    this.cancelled.emit();
  }
}
