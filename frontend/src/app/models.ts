export interface Organization {
  id: string;
  name: string;
  domain?: string | null;
  industry?: string | null;
  plan?: string | null;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ClassificationResult {
  evidence_id?: string;
  primary_controls: string[];
  confidence: number;
  pipeline_run_id?: string;
  created_tasks?: string[];
  cache_hit?: boolean;
  stub?: boolean;
  similarity?: number;
  content_hash?: string;
}

export interface Evidence {
  id: string;
  organization_id: string;
  uploaded_by_id?: string | null;
  title: string;
  description?: string | null;
  evidence_type_id?: string | null;
  source_type_id?: string | null;
  storage_path?: string;
  file_size?: number | null;
  status: string;
  extracted_text?: string | null;
  ai_classification?: ClassificationResult | null;
  created_at?: string;
  updated_at?: string;
}

export interface EvidenceCreatePayload {
  organization_id: string;
  uploaded_by?: string | null;
  title?: string;
  description?: string | null;
  evidence_type_id?: string | null;
  source_type_id?: string | null;
  raw_text?: string | null;
  raw_json?: unknown;
  file_size?: number | null;
}

export interface EvidenceResponse {
  evidence: Evidence;
  classification?: ClassificationResult;
}

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface OrganizationMembership {
  organization: Organization;
  role: 'admin' | 'member';
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
  memberships: OrganizationMembership[];
  active_organization_id?: string;
}
