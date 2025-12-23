import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';

import { PromptTemplate } from './models';

@Component({
  selector: 'app-prompt-management',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="card">
      <div class="section-header">
        <div>
          <p class="eyebrow">Prompts</p>
          <h3>Prompt registry</h3>
        </div>
        <div class="actions">
          <span class="chip">{{ prompts.length }} items</span>
        </div>
      </div>

      <div *ngIf="loading" class="subdued">Loading prompts…</div>
      <div *ngIf="error" class="error">{{ error }}</div>

      <div class="table-wrapper" *ngIf="prompts.length">
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Version</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of prompts">
              <td>{{ p.name }}</td>
              <td>{{ p.version }}</td>
              <td>{{ p.updated_at ? (p.updated_at | date: 'short') : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div *ngIf="!prompts.length && !loading" class="subdued">No prompts yet.</div>

      <form class="form" *ngIf="isAdmin" [formGroup]="promptForm" (ngSubmit)="savePrompt.emit()">
        <div class="section-header">
          <div>
            <p class="eyebrow">Add prompt</p>
            <h4>Create new</h4>
          </div>
          <button class="btn-primary" type="submit" [disabled]="promptForm.invalid">Create</button>
        </div>
        <div class="form-row two-col">
          <div>
            <label>Name</label>
            <input class="input" formControlName="name" placeholder="classifier-default" />
          </div>
          <div>
            <label>Version</label>
            <input class="input" formControlName="version" placeholder="1.0" />
          </div>
        </div>
        <div>
          <label>Content</label>
          <textarea class="input" formControlName="content" placeholder="Prompt template text"></textarea>
        </div>
        <div>
          <label>Metadata (JSON)</label>
          <textarea class="input" formControlName="metadata" placeholder='{"notes":"optional"}'></textarea>
        </div>
      </form>
    </div>
  `,
})
export class PromptManagementComponent {
  @Input() prompts: PromptTemplate[] = [];
  @Input() loading = false;
  @Input() error: string | null = null;
  @Input() promptForm!: FormGroup;
  @Input() isAdmin = false;

  @Output() savePrompt = new EventEmitter<void>();
}
