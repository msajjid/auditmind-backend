import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
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
  AgentRunWithSteps,
  AiPipelineRun,
  EvidenceEvent,
  OrganizationMembershipDetail,
  JobStatus,
  PromptTemplate,
  ModelEntry,
  TaskItem,
} from './models';
import { ApiService } from './services/api.service';
import { EventLogComponent } from './event-log.component';
import { OrganizationFormComponent } from './organization-form.component';
import { UserManagementComponent } from './user-management.component';
import { PromptManagementComponent } from './prompt-management.component';
import { ModelManagementComponent } from './model-management.component';
import { TaskManagementComponent } from './task-management.component';

interface PipelineStage {
  key: string;
  label: string;
  detail: string;
}

interface KeyValuePair {
  key: string;
  value: string;
}

type ThemePreference = 'light' | 'dark' | 'system';
type ActiveTheme = 'light' | 'dark';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    OrganizationFormComponent,
    UserManagementComponent,
    PromptManagementComponent,
    ModelManagementComponent,
    TaskManagementComponent,
    EventLogComponent,
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'AuditMind Evidence Cockpit';
  themePreference: ThemePreference = 'system';
  resolvedTheme: ActiveTheme = 'dark';
  private systemMediaQuery?: MediaQueryList;
  private systemMediaHandler = () => {
    if (this.themePreference === 'system') {
      this.applyTheme();
    }
  };
  private daylightTimer: any;

  organizations: Organization[] = [];
  evidenceList: Evidence[] = [];
  selectedOrgId: string | null = null;
  memberships: OrganizationMembership[] = [];
  currentUser: AuthUser | null = null;
  authToken: string | null = null;
  authMode: 'login' | 'signup' = 'signup';
  viewMode: 'dashboard' | 'organization' | 'user-management' | 'settings' | 'tasks' | 'event-log' = 'dashboard';
  showOrgModal = false;
  expandedEvidenceId: string | null = null;
  detailTab: 'runs' | 'events' = 'runs';
  settingsTab: 'prompts' | 'models' = 'prompts';

  loading = {
    orgs: false,
    evidence: false,
    createOrg: false,
    upload: false,
    classifyId: '' as string | null,
  };

  toast: { kind: 'success' | 'error' | 'info'; message: string } | null = null;
  stageInfoOpenId: string | null = null;
  runsState: Record<
    string,
    { runs: AgentRunWithSteps[]; loading: boolean; error?: string | null; selectedRunId?: string | null }
  > = {};
  eventsState: Record<
    string,
    { events: EvidenceEvent[]; loading: boolean; error?: string | null; filter?: string | 'all' }
  > = {};
  membershipState: Record<string, { members: OrganizationMembershipDetail[]; loading: boolean; error?: string | null }> = {};
  jobState: Record<string, JobStatus & { lastChecked?: number }> = {};
  jobTimers: Record<string, any> = {};
  prompts: PromptTemplate[] = [];
  models: ModelEntry[] = [];
  registryLoading = { prompts: false, models: false };
  registryError: { prompts?: string | null; models?: string | null } = {};
  tasks: TaskItem[] = [];
  tasksLoading = false;
  tasksError: string | null = null;
  readonly displayTitleFn = (evidence: Evidence) => this.displayTitle(evidence);
  readonly primaryControlsFn = (evidence: Evidence) => this.primaryControls(evidence);
  orgSearchTerm = '';
  orgPage = 0;
  readonly orgPageSize = 5;
  selectedFile: File | null = null;
  fileError: string | null = null;

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
  });

  inviteForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    role: ['member', Validators.required],
  });

  promptForm = this.fb.group({
    name: ['', Validators.required],
    version: ['', Validators.required],
    content: ['', Validators.required],
    metadata: [''],
  });

  modelForm = this.fb.group({
    name: ['', Validators.required],
    provider: ['', Validators.required],
    version: ['', Validators.required],
    model_type: ['llm'],
    embedding_dims: [''],
    metadata: [''],
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
    this.initTheme();
    const stored = localStorage.getItem('am_token');
    if (stored) {
      this.authToken = stored;
      this.fetchProfile();
    }
  }

  ngOnDestroy(): void {
    this.teardownSystemListener();
    if (this.daylightTimer) {
      clearInterval(this.daylightTimer);
    }
  }

  setThemePreference(pref: ThemePreference): void {
    this.themePreference = pref;
    localStorage.setItem('am_theme_pref', pref);
    this.applyTheme(true);
  }

  loadOrganizations(): void {
    if (!this.authToken) {
      return;
    }
    this.loading.orgs = true;
    this.api.getOrganizations().subscribe({
      next: (orgs) => {
        this.organizations = orgs;
        this.orgPage = 0;
        this.applyActiveOrganization();
        if (orgs.length) {
          this.loadRegistry();
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

  private initTheme(): void {
    const stored = localStorage.getItem('am_theme_pref');
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      this.themePreference = stored;
    }
    this.applyTheme(true);
  }

  private resolveTheme(): ActiveTheme {
    if (this.themePreference === 'light' || this.themePreference === 'dark') {
      return this.themePreference;
    }
    const prefersDark = typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
      : false;
    if (prefersDark) {
      return 'dark';
    }
    const hour = new Date().getHours();
    return hour >= 7 && hour < 19 ? 'light' : 'dark';
  }

  private applyTheme(setupListeners = false): void {
    this.resolvedTheme = this.resolveTheme();
    document.documentElement.setAttribute('data-theme', this.resolvedTheme);

    if (this.themePreference === 'system') {
      if (setupListeners) {
        this.setupSystemListener();
        this.startDaylightTimer();
      }
    } else {
      this.teardownSystemListener();
      if (this.daylightTimer) {
        clearInterval(this.daylightTimer);
        this.daylightTimer = null;
      }
    }
  }

  private setupSystemListener(): void {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return;
    }
    if (!this.systemMediaQuery) {
      this.systemMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      this.systemMediaQuery.addEventListener('change', this.systemMediaHandler);
    }
  }

  private teardownSystemListener(): void {
    if (this.systemMediaQuery) {
      this.systemMediaQuery.removeEventListener('change', this.systemMediaHandler);
      this.systemMediaQuery = undefined;
    }
  }

  private startDaylightTimer(): void {
    if (this.daylightTimer) {
      return;
    }
    this.daylightTimer = setInterval(() => {
      if (this.themePreference === 'system') {
        this.applyTheme();
      }
    }, 30 * 60 * 1000);
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
    localStorage.removeItem('am_active_org');
    this.viewMode = 'dashboard';
    this.showOrgModal = false;
    localStorage.removeItem('am_token');
  }

  selectOrg(orgId: string): void {
    this.selectedOrgId = orgId;
    localStorage.setItem('am_active_org', orgId);
    this.loadEvidence();
    this.loadMemberships(orgId);
    if (this.viewMode === 'tasks') {
      this.loadTasks();
    }
  }

  setOrgSearch(term: string): void {
    this.orgSearchTerm = term || '';
    this.orgPage = 0;
  }

  filteredOrganizations(): Organization[] {
    const term = this.orgSearchTerm.trim().toLowerCase();
    if (!term) {
      return [...this.organizations];
    }
    return this.organizations.filter((org) => {
      const domain = org.domain || '';
      const plan = org.plan || '';
      const haystack = `${org.name} ${domain} ${plan}`.toLowerCase();
      return haystack.includes(term);
    });
  }

  visibleOrganizations(): Organization[] {
    const list = this.filteredOrganizations();
    if (!list.length) return [];
    const page = Math.max(0, Math.min(this.orgPage, Math.ceil(list.length / this.orgPageSize) - 1));
    const start = page * this.orgPageSize;
    return list.slice(start, start + this.orgPageSize);
  }

  orgTotalPages(): number {
    const total = this.filteredOrganizations().length;
    if (!total) return 0;
    return Math.ceil(total / this.orgPageSize);
  }

  goOrgPage(direction: 'prev' | 'next'): void {
    const totalPages = this.orgTotalPages();
    if (!totalPages) return;
    if (direction === 'prev') {
      this.orgPage = Math.max(0, this.orgPage - 1);
    } else {
      this.orgPage = Math.min(totalPages - 1, this.orgPage + 1);
    }
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

  loadTasks(): void {
    if (!this.selectedOrgId) return;
    this.tasksLoading = true;
    this.tasksError = null;
    this.api.getTasks(this.selectedOrgId).subscribe({
      next: (items) => {
        this.tasks = items;
      },
      error: () => {
        this.tasksError = 'Unable to load tasks.';
      },
      complete: () => (this.tasksLoading = false),
    });
  }

  loadMemberships(orgId?: string | null): void {
    const target = orgId ?? this.selectedOrgId;
    if (!target) return;
    this.membershipState[target] = { members: [], loading: true, error: null };
    this.api.getMemberships(target).subscribe({
      next: (members) => {
        this.membershipState[target] = { members, loading: false, error: null };
      },
      error: () => {
        this.membershipState[target] = { members: [], loading: false, error: 'Unable to load members' };
      },
    });
  }

  loadRegistry(): void {
    this.registryLoading.prompts = true;
    this.registryError.prompts = null;
    this.api.getPrompts().subscribe({
      next: (prompts) => {
        this.prompts = prompts;
        this.registryLoading.prompts = false;
      },
      error: () => {
        this.registryLoading.prompts = false;
        this.registryError.prompts = 'Unable to load prompts';
      },
    });

    this.registryLoading.models = true;
    this.registryError.models = null;
    this.api.getModels().subscribe({
      next: (models) => {
        this.models = models;
        this.registryLoading.models = false;
      },
      error: () => {
        this.registryLoading.models = false;
        this.registryError.models = 'Unable to load models';
      },
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
        this.showOrgModal = false;
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
    if (!this.selectedFile) {
      this.setToast('error', 'Select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('organization_id', this.selectedOrgId);
    formData.append('file', this.selectedFile);
    formData.append('title', this.selectedFile.name);

    this.loading.upload = true;
    this.api.uploadEvidenceFile(formData).subscribe({
      next: (res: EvidenceResponse) => {
        this.mergeEvidence(res.evidence, res.classification);
        this.selectedFile = null;
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

  classifyEvidenceAsync(evidenceId: string): void {
    if (!this.authToken) {
      this.setToast('error', 'Sign in first.');
      return;
    }
    this.jobState[evidenceId] = { job_id: '', status: 'queued', evidence_id: evidenceId };
    this.api.classifyEvidenceAsync(evidenceId).subscribe({
      next: (resp) => {
        this.jobState[evidenceId] = { ...resp, evidence_id: evidenceId };
        this.pollJob(evidenceId, resp.job_id);
        this.setToast('info', 'Classification queued.');
      },
      error: () => {
        this.jobState[evidenceId] = { job_id: '', status: 'failed', evidence_id: evidenceId, error: 'Unable to queue job' };
        this.setToast('error', 'Unable to queue async job.');
      },
    });
  }

  pollJob(evidenceId: string, jobId: string): void {
    if (this.jobTimers[evidenceId]) {
      clearTimeout(this.jobTimers[evidenceId]);
    }
    const tick = () => {
      this.api.getJobStatus(jobId).subscribe({
        next: (status) => {
          this.jobState[evidenceId] = { ...status, evidence_id: evidenceId, lastChecked: Date.now() };
          if (status.status === 'finished' && status.result && typeof status.result === 'object') {
            this.applyClassification(evidenceId, status.result as any);
            return;
          }
          if (status.status === 'failed') {
            return;
          }
          this.jobTimers[evidenceId] = setTimeout(tick, 1500);
        },
        error: () => {
          this.jobState[evidenceId] = { job_id: jobId, status: 'failed', evidence_id: evidenceId, error: 'Poll failed' };
        },
      });
    };
    this.jobTimers[evidenceId] = setTimeout(tick, 1500);
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

  // ---------- Pipeline runs + events ----------
  toggleDetail(evidenceId: string): void {
    if (this.expandedEvidenceId === evidenceId) {
      this.expandedEvidenceId = null;
      return;
    }
    this.expandedEvidenceId = evidenceId;
    this.detailTab = 'runs';
    this.ensureTimeline(evidenceId);
  }

  ensureTimeline(evidenceId: string): void {
    const state = this.runsState[evidenceId];
    if (state?.runs?.length && !state.loading && this.eventsState[evidenceId]?.events?.length) return;

    this.runsState[evidenceId] = { runs: [], loading: true, error: null, selectedRunId: null };
    this.eventsState[evidenceId] = { events: [], loading: true, error: null, filter: 'all' };

    this.api.getTimelineForEvidence(evidenceId).subscribe({
      next: (resp) => {
        this.runsState[evidenceId] = {
          runs: resp.runs,
          loading: false,
          error: null,
          selectedRunId: resp.runs.length ? resp.runs[0].id : null,
        };
        this.eventsState[evidenceId] = { events: resp.events, loading: false, error: null, filter: 'all' };
      },
      error: () => {
        this.runsState[evidenceId] = { runs: [], loading: false, error: 'Unable to load runs', selectedRunId: null };
        this.eventsState[evidenceId] = { events: [], loading: false, error: 'Unable to load events', filter: 'all' };
      },
    });
  }

  ensureEvents(evidenceId: string): void {
    const state = this.eventsState[evidenceId];
    if (state?.events?.length && !state.loading) return;
    this.eventsState[evidenceId] = { events: [], loading: true, error: null, filter: 'all' };
    // now loaded via ensureTimeline; keep method for safety/no-op
    this.eventsState[evidenceId] = { events: state?.events || [], loading: false, error: state?.error, filter: 'all' };
  }

  selectRun(evidenceId: string, runId: string): void {
    const state = this.runsState[evidenceId];
    if (!state) return;
    this.runsState[evidenceId] = { ...state, selectedRunId: runId };
  }

  activeRun(evidenceId: string): AgentRunWithSteps | null {
    const state = this.runsState[evidenceId];
    if (!state?.runs?.length || !state.selectedRunId) return null;
    return state.runs.find((r) => r.id === state.selectedRunId) || null;
  }

  runDuration(start?: string, end?: string): string {
    if (!start || !end) return '—';
    const s = new Date(start).getTime();
    const f = new Date(end).getTime();
    if (Number.isNaN(s) || Number.isNaN(f) || f < s) return '—';
    const secs = Math.max(0, (f - s) / 1000);
    if (secs < 1) return `${Math.round(secs * 1000)} ms`;
    if (secs < 60) return `${secs.toFixed(1)} s`;
    const mins = secs / 60;
    return `${mins.toFixed(1)} m`;
  }

  stepDuration(step: { started_at?: string; finished_at?: string }): string {
    return this.runDuration(step.started_at, step.finished_at);
  }

  preview(obj?: Record<string, unknown> | null): string {
    if (!obj) return '—';
    try {
      const s = JSON.stringify(obj, null, 2);
      return s.length > 320 ? s.slice(0, 320) + '…' : s;
    } catch {
      return '—';
    }
  }

  eventTypes(evidenceId: string): string[] {
    const events = this.eventsForRun(evidenceId);
    return Array.from(new Set(events.map((e) => e.event_type)));
  }

  filteredEvents(evidenceId: string): EvidenceEvent[] {
    const state = this.eventsState[evidenceId];
    if (!state) return [];
    const baseEvents = this.eventsForRun(evidenceId);
    const filter = state.filter || 'all';
    const events = filter === 'all' ? baseEvents : baseEvents.filter((e) => e.event_type === filter);
    return [...events].sort((a, b) => {
      const aTime = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bTime = b.created_at ? new Date(b.created_at).getTime() : 0;
      return bTime - aTime;
    });
  }

  private eventsForRun(evidenceId: string): EvidenceEvent[] {
    const state = this.eventsState[evidenceId];
    const runState = this.runsState[evidenceId];
    if (!state?.events?.length) return [];

    const selectedRun =
      runState?.runs?.find((r) => r.id === runState.selectedRunId) || runState?.runs?.[0] || null;
    const pipelineId = selectedRun?.pipeline_run?.id || selectedRun?.id || null;
    if (!pipelineId) return state.events;

    return state.events.filter((ev) => {
      const evPipelineId = this.eventPipelineId(ev);
      return evPipelineId ? evPipelineId === pipelineId : false;
    });
  }

  private eventPipelineId(event: EvidenceEvent): string | null {
    const direct = (event as any).pipeline_run_id || (event as any).pipelineRunId;
    if (typeof direct === 'string' && direct.trim()) return direct.trim();

    const payload = event.payload || {};
    const candidateKeys = ['pipeline_run_id', 'pipeline_run', 'pipelineRunId', 'run_id'];
    for (const key of candidateKeys) {
      const val = (payload as any)[key];
      if (typeof val === 'string' && val.trim()) return val.trim();
      if (val && typeof val === 'object' && typeof (val as any).id === 'string') {
        const nested = (val as any).id;
        if (nested.trim()) return nested.trim();
      }
    }
    return null;
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

  roleForOrg(orgId?: string | null): 'admin' | 'member' | 'viewer' | null {
    const target = orgId || this.selectedOrgId;
    if (!target) return null;
    const mem = this.memberships.find((m) => m.organization.id === target);
    return mem ? mem.role : null;
  }

  canContribute(orgId?: string | null): boolean {
    const role = this.roleForOrg(orgId);
    return role === 'admin' || role === 'member';
  }

  isAdminAnywhere(): boolean {
    return this.memberships.some((m) => m.role === 'admin');
  }

  setView(mode: 'dashboard' | 'organization' | 'user-management' | 'settings' | 'tasks' | 'event-log'): void {
    this.viewMode = mode;
    if (mode === 'dashboard') {
      this.applyActiveOrganization();
    }
    if (mode === 'event-log' && this.selectedOrgId) {
      this.loadEvidence();
    }
    if (mode === 'user-management' && this.selectedOrgId) {
      this.loadMemberships(this.selectedOrgId);
    }
    if (mode === 'settings') {
      this.loadRegistry();
    }
    if (mode === 'tasks' && this.selectedOrgId) {
      this.loadTasks();
    }
  }

  setSettingsTab(tab: 'prompts' | 'models'): void {
    this.settingsTab = tab;
    this.loadRegistry();
  }

  setTab(tab: 'runs' | 'events'): void {
    this.detailTab = tab;
  }

  setEventFilter(evidenceId: string, filter: string): void {
    const state = this.eventsState[evidenceId];
    if (!state) return;
    this.eventsState[evidenceId] = { ...state, filter };
  }

  toggleStageInfo(evidenceId: string): void {
    this.stageInfoOpenId = this.stageInfoOpenId === evidenceId ? null : evidenceId;
  }

  private setToast(kind: 'success' | 'error' | 'info', message: string): void {
    this.toast = { kind, message };
    setTimeout(() => {
      this.toast = null;
    }, 4200);
  }

  private applyActiveOrganization(): void {
    const stored = localStorage.getItem('am_active_org');
    const storedValid = stored && this.organizations.some((o) => o.id === stored);
    const selectedValid = this.selectedOrgId && this.organizations.some((o) => o.id === this.selectedOrgId);

    let targetId: string | null = null;
    if (storedValid) {
      targetId = stored as string;
    } else if (selectedValid) {
      targetId = this.selectedOrgId;
    } else if (this.organizations.length) {
      targetId = this.organizations[0].id;
    }

    if (!targetId) return;

    const changed = targetId !== this.selectedOrgId;
    this.selectedOrgId = targetId;
    localStorage.setItem('am_active_org', targetId);

    if (changed) {
      this.loadEvidence();
      this.loadMemberships(targetId);
    }
  }

  summarizePayload(obj?: Record<string, unknown> | null, limit = 4): KeyValuePair[] {
    if (!obj) return [];
    const pairs: KeyValuePair[] = [];
    for (const [key, value] of Object.entries(obj)) {
      const rendered = this.renderValue(value);
      if (rendered) {
        pairs.push({ key, value: rendered });
      }
      if (pairs.length >= limit) break;
    }
    return pairs;
  }

  eventTone(eventType?: string): 'success' | 'warn' | 'danger' {
    if (!eventType) return 'warn';
    const lower = eventType.toLowerCase();
    if (lower.includes('fail') || lower.includes('error')) return 'danger';
    if (lower.includes('queue') || lower.includes('start')) return 'warn';
    return 'success';
  }

  statusBadgeClass(status?: string | null): string {
    const tone = (status || '').toLowerCase();
    if (!tone) return 'badge-warn';
    if (tone.includes('fail') || tone.includes('error')) return 'badge-danger';
    if (tone.includes('complete') || tone.includes('success')) return 'badge-success';
    return 'badge-warn';
  }

  runLabel(
    run?: {
      pipeline_run?: AiPipelineRun | null;
      agent_name?: string | null;
      id?: string | null;
      started_at?: string | null;
      created_at?: string | null;
    } | null,
  ): string {
    if (!run) return 'Run';
    const typeRaw = run.pipeline_run?.pipeline_type || run.agent_name || 'Run';
    const typeLabel = this.humanizeLabel(typeRaw);
    const timestamp = this.runTimestamp(run);
    return timestamp ? `${timestamp} · ${typeLabel}` : typeLabel;
  }

  shortId(id?: string | null): string {
    if (!id) return '—';
    return id.length > 8 ? `${id.slice(0, 8)}…` : id;
  }

  private runTimestamp(run: {
    pipeline_run?: AiPipelineRun | null;
    started_at?: string | null;
    created_at?: string | null;
  }): string {
    const ts = run.started_at || run.pipeline_run?.started_at || run.pipeline_run?.created_at || run.created_at;
    return ts ? this.formatTimestamp(ts) : '';
  }

  private formatTimestamp(value?: string | null): string {
    if (!value) return '';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return '';
    return parsed.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  private humanizeLabel(text: string): string {
    const cleaned = text.replace(/[_-]+/g, ' ').trim();
    if (!cleaned) return 'Run';
    return cleaned
      .split(' ')
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  displayTitle(evidence: Evidence): string {
    const controls = this.primaryControls(evidence);
    const controlLabel = this.primaryControlLabel(controls);
    const tag = evidence.tags?.find((t) => t && t.trim());
    if (tag) {
      return this.composeTitle(tag.trim(), controlLabel, 30);
    }

    const raw = evidence.title?.trim() || '';
    if (raw && !this.looksLikeJson(raw)) {
      return this.composeTitle(raw, controlLabel, 42);
    }

    if (raw && this.looksLikeJson(raw)) {
      const jsonTitle = this.titleFromJson(raw);
      if (jsonTitle) {
        return this.composeTitle(jsonTitle, controlLabel, 42);
      }
    }

    if (evidence.description?.trim()) {
      return this.composeTitle(evidence.description.trim(), controlLabel, 42);
    }

    if (evidence.extracted_text?.trim()) {
      return this.composeTitle(evidence.extracted_text.trim(), controlLabel, 42);
    }

    if (controlLabel) {
      return `${controlLabel} evidence`;
    }

    return `Evidence ${this.shortId(evidence.id)}`;
  }

  private composeTitle(body: string, controlLabel?: string | null, maxLength = 60): string {
    let budget = maxLength;
    if (controlLabel) {
      // Reserve space so the control hint + title stay compact.
      budget = Math.max(24, maxLength - controlLabel.length - 3);
    }
    const trimmed = this.truncateLabel(body, budget);
    return controlLabel ? `${controlLabel} · ${trimmed}` : trimmed;
  }

  private truncateLabel(text: string, maxLength = 60): string {
    const clean = text.replace(/\s+/g, ' ').trim();
    if (clean.length <= maxLength) return clean;
    const softCut = clean.slice(0, maxLength);
    const lastSpace = softCut.lastIndexOf(' ');
    const sliced = lastSpace > 40 ? softCut.slice(0, lastSpace) : softCut;
    return `${sliced}…`;
  }

  private primaryControlLabel(controls: string[]): string | null {
    if (!controls || !controls.length) return null;
    return controls.length === 1 ? controls[0] : `${controls[0]} +${controls.length - 1}`;
  }

  private looksLikeJson(text: string): boolean {
    const trimmed = text.trim();
    return (
      (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
      (trimmed.startsWith('[') && trimmed.endsWith(']'))
    );
  }

  private titleFromJson(raw: string): string | null {
    try {
      const parsed = JSON.parse(raw);
      return this.extractJsonTitle(parsed);
    } catch {
      return null;
    }
  }

  private extractJsonTitle(value: unknown): string | null {
    if (!value) return null;
    if (typeof value === 'string') return value.trim();
    if (Array.isArray(value)) {
      for (const item of value) {
        const candidate = this.extractJsonTitle(item);
        if (candidate) return candidate;
      }
      return null;
    }
    if (typeof value === 'object') {
      const obj = value as Record<string, unknown>;
      const fields = [
        'title',
        'name',
        'summary',
        'description',
        'id',
        'resource',
        'arn',
        'bucket',
        'path',
        'file',
        'eventName',
        'detail-type',
        'policyName',
        'rule',
      ];
      for (const key of fields) {
        const candidate = obj[key];
        if (typeof candidate === 'string' && candidate.trim()) {
          return candidate.trim();
        }
      }
      const stringValues = Object.values(obj).filter((v) => typeof v === 'string' && v.trim()) as string[];
      if (stringValues.length) return stringValues[0].trim();
    }
    return null;
  }

  private renderValue(value: unknown): string {
    if (value === null || value === undefined) return '';
    if (typeof value === 'string') {
      return value.length > 80 ? `${value.slice(0, 77)}…` : value;
    }
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    if (Array.isArray(value)) return `Array(${value.length})`;
    if (typeof value === 'object') {
      const keys = Object.keys(value as Record<string, unknown>);
      return keys.length ? `Object(${keys.slice(0, 3).join(', ')})` : 'Object';
    }
    return '';
  }

  inviteMember(): void {
    if (!this.selectedOrgId) return;
    if (this.inviteForm.invalid) {
        this.inviteForm.markAllAsTouched();
        return;
    }
    this.api
      .inviteMember(this.selectedOrgId, {
        email: this.inviteForm.value.email as string,
        role: this.inviteForm.value.role as 'admin' | 'member' | 'viewer',
      })
      .subscribe({
      next: () => {
        this.setToast('success', 'Invitation updated/created.');
        this.inviteForm.reset({ role: 'member' });
        this.loadMemberships(this.selectedOrgId);
      },
      error: () => this.setToast('error', 'Unable to invite member.'),
    });
  }

  deactivateMember(membershipId: string): void {
    if (!this.selectedOrgId) return;
    this.api.deactivateMember(this.selectedOrgId, membershipId).subscribe({
      next: () => {
        this.setToast('success', 'Member deactivated.');
        this.loadMemberships(this.selectedOrgId);
      },
      error: () => this.setToast('error', 'Unable to deactivate member.'),
    });
  }

  savePrompt(): void {
    if (this.promptForm.invalid) {
      this.promptForm.markAllAsTouched();
      return;
    }
    let metadata: any = undefined;
    const meta = this.promptForm.value.metadata as string;
    if (meta && meta.trim()) {
      try {
        metadata = JSON.parse(meta);
      } catch {
        this.setToast('error', 'Prompt metadata must be valid JSON.');
        return;
      }
    }
    this.api
      .createPrompt({
        name: this.promptForm.value.name as string,
        version: this.promptForm.value.version as string,
        content: this.promptForm.value.content as string,
        metadata,
      })
      .subscribe({
        next: () => {
          this.setToast('success', 'Prompt saved.');
          this.promptForm.reset({ metadata: '' });
          this.loadRegistry();
        },
        error: () => this.setToast('error', 'Unable to save prompt.'),
      });
  }

  saveModel(): void {
    if (this.modelForm.invalid) {
      this.modelForm.markAllAsTouched();
      return;
    }
    let metadata: any = undefined;
    const meta = this.modelForm.value.metadata as string;
    if (meta && meta.trim()) {
      try {
        metadata = JSON.parse(meta);
      } catch {
        this.setToast('error', 'Model metadata must be valid JSON.');
        return;
      }
    }
    const dimsRaw = this.modelForm.value.embedding_dims as string;
    const embedding_dims = dimsRaw ? Number(dimsRaw) : undefined;

    this.api
      .createModel({
        name: this.modelForm.value.name as string,
        provider: this.modelForm.value.provider as string,
        version: this.modelForm.value.version as string,
        model_type: (this.modelForm.value.model_type as string) || 'llm',
        embedding_dims: Number.isNaN(embedding_dims) ? undefined : embedding_dims,
        metadata,
      })
      .subscribe({
        next: () => {
          this.setToast('success', 'Model saved.');
          this.modelForm.reset({ model_type: 'llm', metadata: '' });
          this.loadRegistry();
        },
        error: () => this.setToast('error', 'Unable to save model.'),
      });
  }

  organizationName(orgId?: string | null): string {
    const target = orgId || this.selectedOrgId;
    if (!target) return '';
    const org = this.organizations.find((o) => o.id === target);
    return org ? org.name : '';
  }
}
