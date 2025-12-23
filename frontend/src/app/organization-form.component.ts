import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-organization-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="card">
      <div class="section-header">
        <div>
          <p class="eyebrow">Organizations</p>
          <h3>Add a new organization</h3>
        </div>
      </div>

      <form class="form" *ngIf="isAdmin; else nonAdmin" [formGroup]="orgForm" (ngSubmit)="createOrg.emit()">
        <div class="form-row two-col">
          <div>
            <label>Name</label>
            <input class="input" formControlName="name" placeholder="Acme Corp" />
          </div>
          <div>
            <label>Domain</label>
            <input class="input" formControlName="domain" placeholder="acme.com" />
          </div>
        </div>
        <div class="form-row two-col">
          <div>
            <label>Industry</label>
            <input class="input" formControlName="industry" placeholder="SaaS, Fintech" />
          </div>
          <div>
            <label>Plan</label>
            <input class="input" formControlName="plan" placeholder="free / pro" />
          </div>
        </div>
        <button class="btn-primary" type="submit" [disabled]="loading">
          {{ loading ? 'Creating…' : 'Create organization' }}
        </button>
      </form>

      <ng-template #nonAdmin>
        <div class="subdued">Organization creation is available to admins only.</div>
      </ng-template>
    </section>
  `,
})
export class OrganizationFormComponent {
  @Input() orgForm!: FormGroup;
  @Input() loading = false;
  @Input() isAdmin = false;
  @Output() createOrg = new EventEmitter<void>();
}
