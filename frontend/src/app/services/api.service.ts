import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
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
  EvidenceEvent,
  OrganizationMembershipDetail,
  JobStatus,
  PromptTemplate,
  ModelEntry,
  TaskItem,
} from '../models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  register(payload: {
    email: string;
    password: string;
    full_name?: string;
    organization_name: string;
    domain?: string;
  }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.baseUrl}/auth/register/`, payload);
  }

  login(payload: { email: string; password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.baseUrl}/auth/login/`, payload);
  }

  me(): Observable<{ user: AuthUser; memberships: OrganizationMembership[] }> {
    return this.http.get<{ user: AuthUser; memberships: OrganizationMembership[] }>(`${this.baseUrl}/auth/me/`);
  }

  getOrganizations(): Observable<Organization[]> {
    return this.http.get<Organization[]>(`${this.baseUrl}/organizations/`);
  }

  createOrganization(payload: Partial<Organization>): Observable<Organization> {
    return this.http.post<Organization>(`${this.baseUrl}/organizations/`, payload);
  }

  getEvidence(organizationId: string): Observable<Evidence[]> {
    const params = new HttpParams().set('organization_id', organizationId);
    return this.http.get<Evidence[]>(`${this.baseUrl}/evidence/`, { params });
  }

  uploadEvidence(payload: EvidenceCreatePayload): Observable<EvidenceResponse> {
    return this.http.post<EvidenceResponse>(`${this.baseUrl}/evidence/`, payload);
  }

  uploadEvidenceFile(form: FormData): Observable<EvidenceResponse> {
    return this.http.post<EvidenceResponse>(`${this.baseUrl}/evidence/upload/`, form);
  }

  classifyEvidence(evidenceId: string): Observable<ClassificationResult> {
    return this.http.post<ClassificationResult>(
      `${this.baseUrl}/evidence/${evidenceId}/classify/`,
      {},
    );
  }

  classifyEvidenceAsync(evidenceId: string): Observable<JobStatus> {
    return this.http.post<JobStatus>(
      `${this.baseUrl}/evidence/${evidenceId}/classify/?async=1`,
      {},
    );
  }

  getTimelineForEvidence(
    evidenceId: string,
  ): Observable<{ runs: AgentRunWithSteps[]; events: EvidenceEvent[] }> {
    return this.http.get<{ runs: AgentRunWithSteps[]; events: EvidenceEvent[] }>(
      `${this.baseUrl}/evidence/${evidenceId}/timeline/`,
    );
  }

  getMemberships(orgId: string): Observable<OrganizationMembershipDetail[]> {
    return this.http.get<OrganizationMembershipDetail[]>(`${this.baseUrl}/organizations/${orgId}/memberships/`);
    }

  inviteMember(orgId: string, payload: { email: string; role: 'admin' | 'member' | 'viewer' }) {
    return this.http.post(`${this.baseUrl}/organizations/${orgId}/memberships/`, payload);
  }

  deactivateMember(orgId: string, membershipId: string) {
    return this.http.post(
      `${this.baseUrl}/organizations/${orgId}/memberships/${membershipId}/deactivate/`,
      {},
    );
  }

  getJobStatus(jobId: string): Observable<JobStatus> {
    return this.http.get<JobStatus>(`${this.baseUrl}/jobs/${jobId}/`);
  }

  getPrompts(): Observable<PromptTemplate[]> {
    return this.http.get<PromptTemplate[]>(`${this.baseUrl}/prompts/`);
  }

  createPrompt(payload: { name: string; version: string; content: string; metadata?: any }): Observable<PromptTemplate> {
    return this.http.post<PromptTemplate>(`${this.baseUrl}/prompts/`, payload);
  }

  getModels(): Observable<ModelEntry[]> {
    return this.http.get<ModelEntry[]>(`${this.baseUrl}/models/`);
  }

  createModel(payload: {
    name: string;
    provider: string;
    version: string;
    model_type?: string;
    embedding_dims?: number | null;
    metadata?: any;
  }): Observable<ModelEntry> {
    return this.http.post<ModelEntry>(`${this.baseUrl}/models/`, payload);
  }

  getTasks(organizationId: string): Observable<TaskItem[]> {
    const params = new HttpParams().set('organization_id', organizationId);
    return this.http.get<TaskItem[]>(`${this.baseUrl}/tasks/`, { params });
  }
}
