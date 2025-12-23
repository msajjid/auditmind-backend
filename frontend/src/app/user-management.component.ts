import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';

import { OrganizationMembershipDetail } from './models';

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="card">
      <div class="section-header">
        <div>
          <p class="eyebrow">Members</p>
          <h3>{{ organizationName || 'Select an organization' }}</h3>
        </div>
        <span class="chip" *ngIf="roleLabel">Role: {{ roleLabel }}</span>
      </div>

      <div *ngIf="loading" class="subdued">Loading members…</div>
      <div *ngIf="error" class="error">{{ error }}</div>

      <div class="table-wrapper" *ngIf="members?.length">
        <table class="table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th *ngIf="isAdmin">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let m of members">
              <td>{{ m.user.first_name || m.user.username || '—' }}</td>
              <td>{{ m.user.email }}</td>
              <td>{{ m.role }}</td>
              <td>{{ m.is_active ? 'Active' : 'Inactive' }}</td>
              <td *ngIf="isAdmin">
                <button class="btn-ghost" (click)="onDeactivate(m.id)" [disabled]="!m.is_active">Deactivate</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div *ngIf="!members?.length && !loading" class="subdued">
        No members yet.
      </div>

      <form class="form" *ngIf="isAdmin" [formGroup]="inviteForm" (ngSubmit)="onInvite()">
        <p class="eyebrow">Invite member</p>
        <div class="form-row two-col">
          <div>
            <label>Email</label>
            <input class="input" formControlName="email" placeholder="user@example.com" />
          </div>
          <div>
            <label>Role</label>
            <select class="input" formControlName="role">
              <option value="admin">admin</option>
              <option value="member">member</option>
              <option value="viewer">viewer</option>
            </select>
          </div>
        </div>
        <button class="btn-primary" type="submit" [disabled]="inviteForm.invalid">Invite</button>
      </form>
    </section>
  `,
})
export class UserManagementComponent {
  @Input() members: OrganizationMembershipDetail[] = [];
  @Input() loading = false;
  @Input() error: string | null = null;
  @Input() isAdmin = false;
  @Input() inviteForm!: FormGroup;
  @Input() organizationName = '';
  @Input() roleLabel: string | null = null;

  @Output() invite = new EventEmitter<void>();
  @Output() deactivate = new EventEmitter<string>();

  onInvite(): void {
    this.invite.emit();
  }

  onDeactivate(id: string): void {
    this.deactivate.emit(id);
  }
}
