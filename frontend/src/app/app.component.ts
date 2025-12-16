import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import {
  AuthResponse,
  AuthUser,
  ClassificationResult,
  Evidence,
  EvidenceCreatePayload,
  EvidenceResponse,
  Organization,
  OrganizationMembership,
} from './models';
import { ApiService } from './services/api.service';

interface PipelineStage {
  key: string;
  label: string;
  detail: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements OnInit {
  title = 'AuditMind Evidence Cockpit';

  organizations: Organization[] = [];
  evidenceList: Evidence[] = [];
  selectedOrgId: string | null = null;
  memberships: OrganizationMembership[] = [];
  currentUser: AuthUser | null = null;
  authToken: string | null = null;
  authMode: 'login' | 'signup' = 'signup';

  loading = {
    orgs: false,
    evidence: false,
    createOrg: false,
    upload: false,
    classifyId: '' as string | null,
  };

  toast: { kind: 'success' | 'error' | 'info'; message: string } | null = null;
  rawJsonError: string | null = null;

  loginForm = this.fb.group({
    email: ['', Validators.required],
    password: ['', Validators.required],
  });

  signupForm = this.fb.group({
    email: ['', Validators.required],
    password: ['', Validators.required],
    full_name: [''],
    organization_name: ['', Validators.required],
    domain: [''],
  });

  orgForm = this.fb.group({
    name: ['', Validators.required],
    domain: [''],
    industry: [''],
    plan: ['free'],
  });

  evidenceForm = this.fb.group({
    rawMode: ['text'],
    raw_text: ['', Validators.required],
    raw_json: [''],
  });

  pipelineStages: PipelineStage[] = [
    { key: 'preprocessing', label: 'Preprocessing', detail: 'Normalize text + hints' },
    { key: 'candidate_retrieval_fts', label: 'Candidate Retrieval', detail: 'FTS lookup on controls' },
    { key: 'control_ranking', label: 'Control Ranking', detail: 'Score and order matches' },
    { key: 'thresholding', label: 'Thresholding', detail: 'Filter weak signals' },
    { key: 'persistence', label: 'Persistence', detail: 'Store outputs & embeddings' },
    { key: 'auto_task_creation', label: 'Task Creation', detail: 'Create remediation tasks' },
  ];

  constructor(private api: ApiService, private fb: FormBuilder) {}

  ngOnInit(): void {
    const stored = localStorage.getItem('am_token');
    if (stored) {
      this.authToken = stored;
      this.fetchProfile();
    }
  }

  loadOrganizations(): void {
    if (!this.authToken) {
      return;
    }
    this.loading.orgs = true;
    this.api.getOrganizations().subscribe({
      next: (orgs) => {
        this.organizations = orgs;
        if (!this.selectedOrgId && orgs.length) {
          this.selectedOrgId = orgs[0].id;
          this.loadEvidence();
        }
      },
      error: () => {
        this.setToast('error', 'Unable to fetch organizations. Confirm backend is running on :8000.');
      },
      complete: () => (this.loading.orgs = false),
    });
  }

  fetchProfile(): void {
    this.api.me().subscribe({
      next: (resp) => {
        this.currentUser = resp.user;
        this.memberships = resp.memberships;
        this.loadOrganizations();
      },
      error: () => {
        this.logout();
      },
    });
  }

  private handleAuthSuccess(res: AuthResponse): void {
    this.authToken = res.token;
    localStorage.setItem('am_token', res.token);
    this.currentUser = res.user;
    this.memberships = res.memberships;
    if (res.active_organization_id) {
      this.selectedOrgId = res.active_organization_id;
    } else if (res.memberships.length) {
      this.selectedOrgId = res.memberships[0].organization.id;
    }
    this.loadOrganizations();
    this.setToast('success', 'Signed in.');
  }

  login(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }
    this.api.login(this.loginForm.value as { email: string; password: string }).subscribe({
      next: (res) => this.handleAuthSuccess(res),
      error: () => this.setToast('error', 'Login failed. Check your credentials.'),
    });
  }

  signup(): void {
    if (this.signupForm.invalid) {
      this.signupForm.markAllAsTouched();
      return;
    }
    this.api
      .register(this.signupForm.value as {
        email: string;
        password: string;
        full_name?: string;
        organization_name: string;
        domain?: string;
      })
      .subscribe({
        next: (res) => this.handleAuthSuccess(res),
        error: () => this.setToast('error', 'Sign up failed. Email may already exist.'),
      });
  }

  logout(): void {
    this.authToken = null;
    this.currentUser = null;
    this.memberships = [];
    this.organizations = [];
    this.evidenceList = [];
    this.selectedOrgId = null;
    localStorage.removeItem('am_token');
  }

  selectOrg(orgId: string): void {
    this.selectedOrgId = orgId;
    this.loadEvidence();
  }

  loadEvidence(): void {
    if (!this.authToken) return;
    if (!this.selectedOrgId) {
      return;
    }
    this.loading.evidence = true;
    this.api.getEvidence(this.selectedOrgId).subscribe({
      next: (items) => {
        this.evidenceList = items;
      },
      error: () => this.setToast('error', 'Failed to load evidence for this organization.'),
      complete: () => (this.loading.evidence = false),
    });
  }

  submitOrganization(): void {
    if (!this.authToken) {
      this.setToast('error', 'Sign in first.');
      return;
    }
    if (this.orgForm.invalid) {
      this.orgForm.markAllAsTouched();
      return;
    }

    const payload: Partial<Organization> = {
      name: this.orgForm.value.name?.trim() || undefined,
      domain: this.orgForm.value.domain?.trim() || undefined,
      industry: this.orgForm.value.industry?.trim() || undefined,
      plan: this.orgForm.value.plan?.trim() || undefined,
    };

    this.loading.createOrg = true;
    this.api.createOrganization(payload).subscribe({
      next: (org) => {
        this.organizations = [org, ...this.organizations];
        this.selectedOrgId = org.id;
        this.orgForm.reset({ plan: 'free' });
        this.setToast('success', `Created organization ${org.name}.`);
        this.loadEvidence();
      },
      error: () => this.setToast('error', 'Could not create organization.'),
      complete: () => (this.loading.createOrg = false),
    });
  }

  submitEvidence(): void {
    if (!this.authToken) {
      this.setToast('error', 'Sign in first.');
      return;
    }
    if (!this.selectedOrgId) {
      this.setToast('error', 'Select or create an organization first.');
      return;
    }

    const rawMode = this.evidenceForm.value.rawMode;
    const payload: EvidenceCreatePayload = {
      organization_id: this.selectedOrgId,
    };

    if (rawMode === 'json') {
      try {
        payload.raw_json = this.evidenceForm.value.raw_json
          ? JSON.parse(this.evidenceForm.value.raw_json)
          : {};
        this.rawJsonError = null;
      } catch (err) {
        this.rawJsonError = 'Invalid JSON payload.';
        return;
      }
    } else {
      const rawText = this.evidenceForm.value.raw_text?.trim();
      if (rawText) {
        payload.raw_text = rawText;
      }
    }

    if (!payload.raw_text && payload.raw_json === undefined) {
      this.setToast('error', 'Provide either raw text or valid JSON content.');
      return;
    }

    this.loading.upload = true;
    this.api.uploadEvidence(payload).subscribe({
      next: (res: EvidenceResponse) => {
        this.mergeEvidence(res.evidence, res.classification);
        this.evidenceForm.reset({ rawMode: 'text' });
        this.setToast('success', 'Evidence uploaded and classified.');
      },
      error: () => this.setToast('error', 'Upload failed. Ensure backend is reachable.'),
      complete: () => (this.loading.upload = false),
    });
  }

  classifyEvidence(evidenceId: string): void {
    if (!this.authToken) {
      this.setToast('error', 'Sign in first.');
      return;
    }
    this.loading.classifyId = evidenceId;
    this.api.classifyEvidence(evidenceId).subscribe({
      next: (result) => {
        this.applyClassification(evidenceId, result);
        this.setToast('success', 'Classification refreshed.');
      },
      error: () => this.setToast('error', 'Classification failed for this evidence.'),
      complete: () => (this.loading.classifyId = null),
    });
  }

  mergeEvidence(evidence: Evidence, classification?: ClassificationResult): void {
    const enriched = classification ? { ...evidence, ai_classification: classification } : evidence;
    const existingIndex = this.evidenceList.findIndex((item) => item.id === evidence.id);
    if (existingIndex >= 0) {
      this.evidenceList = [
        ...this.evidenceList.slice(0, existingIndex),
        enriched,
        ...this.evidenceList.slice(existingIndex + 1),
      ];
    } else {
      this.evidenceList = [enriched, ...this.evidenceList];
    }
  }

  applyClassification(evidenceId: string, classification: ClassificationResult): void {
    const target = this.evidenceList.find((item) => item.id === evidenceId);
    if (!target) {
      return;
    }
    target.ai_classification = classification;
    target.status = 'classified';
    this.evidenceList = [...this.evidenceList];
  }

  getPipelineState(evidence: Evidence): Array<PipelineStage & { status: 'done' | 'active' | 'pending' }> {
    const hasClassification = Boolean(evidence.ai_classification);
    return this.pipelineStages.map((stage, idx) => ({
      ...stage,
      status: hasClassification ? 'done' : idx === 0 ? 'active' : 'pending',
    }));
  }

  primaryControls(evidence: Evidence): string[] {
    return evidence.ai_classification?.primary_controls || [];
  }

  confidenceLabel(evidence: Evidence): string {
    const confidence = evidence.ai_classification?.confidence;
    if (confidence === undefined || confidence === null) return '—';
    return `${Math.round(confidence * 100)}% confidence`;
  }

  trackEvidenceById(_: number, item: Evidence): string {
    return item.id;
  }

  trackOrgById(_: number, org: Organization): string {
    return org.id;
  }

  get classifiedCount(): number {
    return this.evidenceList.filter((e) => !!e.ai_classification).length;
  }

  isAdminForOrg(orgId?: string | null): boolean {
    const target = orgId || this.selectedOrgId;
    if (!target) return false;
    return this.memberships.some((m) => m.organization.id === target && m.role === 'admin');
  }

  private setToast(kind: 'success' | 'error' | 'info', message: string): void {
    this.toast = { kind, message };
    setTimeout(() => {
      this.toast = null;
    }, 4200);
  }
}
