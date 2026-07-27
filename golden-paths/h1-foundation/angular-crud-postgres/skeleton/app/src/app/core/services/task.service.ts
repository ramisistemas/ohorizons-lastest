import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Task, TaskInput } from '../models/task.model';

/**
 * Cliente CRUD genérico contra un recurso PostgREST.
 * PostgREST traduce cada verbo HTTP directo a SQL sobre la tabla `environment.resource`:
 *   GET    /tasks             -> SELECT *
 *   GET    /tasks?id=eq.1     -> SELECT * WHERE id = 1
 *   POST   /tasks             -> INSERT
 *   PATCH  /tasks?id=eq.1     -> UPDATE WHERE id = 1
 *   DELETE /tasks?id=eq.1     -> DELETE WHERE id = 1
 */
@Injectable({ providedIn: 'root' })
export class TaskService {
  private readonly baseUrl = `${environment.apiUrl}/${environment.resource}`;

  // Pide de vuelta la fila creada/actualizada en la misma respuesta.
  private readonly returnRepresentation = new HttpHeaders({
    Prefer: 'return=representation',
  });

  constructor(private readonly http: HttpClient) {}

  list(): Observable<Task[]> {
    return this.http.get<Task[]>(this.baseUrl, {
      params: { order: 'created_at.desc' },
    });
  }

  create(input: TaskInput): Observable<Task[]> {
    return this.http.post<Task[]>(this.baseUrl, input, {
      headers: this.returnRepresentation,
    });
  }

  update(id: number, input: TaskInput): Observable<Task[]> {
    return this.http.patch<Task[]>(this.baseUrl, input, {
      headers: this.returnRepresentation,
      params: { id: `eq.${id}` },
    });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(this.baseUrl, {
      params: { id: `eq.${id}` },
    });
  }
}
