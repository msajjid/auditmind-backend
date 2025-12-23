import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

import { TaskItem } from './models';

@Component({
  selector: 'app-task-management',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card">
      <div class="section-header">
        <div>
          <p class="eyebrow">Tasks</p>
          <h3>Auto-created follow-ups</h3>
        </div>
        <span class="chip">{{ tasks.length }} items</span>
      </div>

      <div *ngIf="loading" class="subdued">Loading tasks…</div>
      <div *ngIf="error" class="error">{{ error }}</div>

      <div class="task-grid" *ngIf="tasks.length">
        <div class="task-card" *ngFor="let task of tasks">
          <div class="task-header">
            <div class="task-title">{{ task.title }}</div>
            <span class="badge" [ngClass]="task.status === 'open' ? 'badge-warn' : 'badge-success'">
              {{ task.status }}
            </span>
          </div>
          <div class="subdued" *ngIf="task.control_reference || task.framework_code">
            {{ task.framework_code || 'Framework' }} · {{ task.control_reference || 'Control' }}
          </div>
          <div class="subdued" *ngIf="task.control_title">{{ task.control_title }}</div>
          <div class="meta-row">
            <span *ngIf="task.evidence_title">Evidence: {{ task.evidence_title }}</span>
            <span>Created {{ task.created_at ? (task.created_at | date:'short') : '—' }}</span>
          </div>
          <p class="subdued" *ngIf="task.description">{{ task.description }}</p>
        </div>
      </div>

      <div *ngIf="!tasks.length && !loading" class="subdued">No tasks yet for this organization.</div>
    </div>
  `,
  styles: [
    `
      .task-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 12px;
        margin-top: 10px;
      }
      .task-card {
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px 14px;
        background: rgba(255, 255, 255, 0.02);
        display: grid;
        gap: 8px;
      }
      .task-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
      }
      .task-title {
        font-weight: 700;
      }
      .meta-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        font-size: 12px;
        color: var(--muted);
      }
    `,
  ],
})
export class TaskManagementComponent {
  @Input() tasks: TaskItem[] = [];
  @Input() loading = false;
  @Input() error: string | null = null;
}
