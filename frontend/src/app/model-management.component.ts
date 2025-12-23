import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';

import { ModelEntry } from './models';

@Component({
  selector: 'app-model-management',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="card">
      <div class="section-header">
        <div>
          <p class="eyebrow">Models</p>
          <h3>Model registry</h3>
        </div>
        <div class="actions">
          <span class="chip">{{ models.length }} items</span>
        </div>
      </div>

      <div *ngIf="loading" class="subdued">Loading models…</div>
      <div *ngIf="error" class="error">{{ error }}</div>

      <div class="table-wrapper" *ngIf="models.length">
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Provider</th>
              <th>Version</th>
              <th>Type</th>
              <th>Dims</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let m of models">
              <td>{{ m.name }}</td>
              <td>{{ m.provider }}</td>
              <td>{{ m.version }}</td>
              <td>{{ m.model_type }}</td>
              <td>{{ m.embedding_dims || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div *ngIf="!models.length && !loading" class="subdued">No models yet.</div>

      <form class="form" *ngIf="isAdmin" [formGroup]="modelForm" (ngSubmit)="saveModel.emit()">
        <div class="section-header">
          <div>
            <p class="eyebrow">Add model</p>
            <h4>Create new</h4>
          </div>
          <button class="btn-primary" type="submit" [disabled]="modelForm.invalid">Create</button>
        </div>
        <div class="form-row two-col">
          <div>
            <label>Name</label>
            <input class="input" formControlName="name" placeholder="gpt-4o-mini" />
          </div>
          <div>
            <label>Provider</label>
            <input class="input" formControlName="provider" placeholder="openai" />
          </div>
        </div>
        <div class="form-row two-col">
          <div>
            <label>Version</label>
            <input class="input" formControlName="version" placeholder="2024-06-01" />
          </div>
          <div>
            <label>Model type</label>
            <select class="input" formControlName="model_type">
              <option value="llm">llm</option>
              <option value="embedding">embedding</option>
            </select>
          </div>
        </div>
        <div class="form-row two-col">
          <div>
            <label>Embedding dims (optional)</label>
            <input class="input" formControlName="embedding_dims" placeholder="1536" />
          </div>
          <div>
            <label>Metadata (JSON)</label>
            <textarea class="input" formControlName="metadata" placeholder='{"notes":"optional"}'></textarea>
          </div>
        </div>
      </form>
    </div>
  `,
})
export class ModelManagementComponent {
  @Input() models: ModelEntry[] = [];
  @Input() loading = false;
  @Input() error: string | null = null;
  @Input() modelForm!: FormGroup;
  @Input() isAdmin = false;

  @Output() saveModel = new EventEmitter<void>();
}
