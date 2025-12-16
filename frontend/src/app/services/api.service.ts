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

  classifyEvidence(evidenceId: string): Observable<ClassificationResult> {
    return this.http.post<ClassificationResult>(
      `${this.baseUrl}/evidence/${evidenceId}/classify/`,
      {},
    );
  }
}
