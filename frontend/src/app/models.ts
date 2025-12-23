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
  agent_run_id?: string;
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
  tags?: string[] | null;
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
  role: 'admin' | 'member' | 'viewer';
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

export interface AgentStepLog {
  id: string;
  step_name: string;
  status: string;
  started_at?: string;
  finished_at?: string;
  input_snapshot?: Record<string, unknown> | null;
  output_snapshot?: Record<string, unknown> | null;
  error?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface AiPipelineRun {
  id: string;
  pipeline_type: string;
  status: string;
  started_at?: string;
  finished_at?: string;
  details?: Record<string, unknown> | null;
  created_at?: string;
  updated_at?: string;
}

export interface AgentRun {
  id: string;
  agent_name: string;
  agent_version?: string | null;
  status: string;
  started_at?: string;
  finished_at?: string;
  details?: Record<string, unknown> | null;
  pipeline_run?: AiPipelineRun | null;
  evidence_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AgentRunWithSteps extends AgentRun {
  step_logs: AgentStepLog[];
}

export interface EvidenceEvent {
  id: string;
  event_type: string;
  evidence_id?: string;
  organization_id?: string;
  payload?: Record<string, unknown> | null;
  created_at?: string;
}

export interface OrganizationMembershipDetail {
  id: string;
  user: AuthUser;
  role: 'admin' | 'member' | 'viewer';
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'started' | 'finished' | 'failed' | string;
  evidence_id?: string;
  result?: unknown;
  error?: string;
}

export interface PromptTemplate {
  id: string;
  name: string;
  version: string;
  content: string;
  metadata?: Record<string, unknown> | null;
  created_at?: string;
  updated_at?: string;
}

export interface ModelEntry {
  id: string;
  name: string;
  provider: string;
  version: string;
  model_type: string;
  embedding_dims?: number | null;
  metadata?: Record<string, unknown> | null;
  created_at?: string;
  updated_at?: string;
}

export interface TaskItem {
  id: string;
  organization_id: string;
  framework_id?: string | null;
  framework_code?: string | null;
  control_id?: string | null;
  control_reference?: string | null;
  control_title?: string | null;
  evidence_id?: string | null;
  evidence_title?: string | null;
  title: string;
  description?: string | null;
  status: string;
  assignee_id?: string | null;
  due_date?: string | null;
  created_at?: string;
  updated_at?: string;
}
