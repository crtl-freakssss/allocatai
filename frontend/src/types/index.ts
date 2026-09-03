export interface MetaData {
  request_id: string;
  schema_version?: string;
  timestamp?: string;
  pagination?: {
    page: number;
    page_size: number;
    total: number;
  } | null;
}

export interface ApiResponse<T> {
  data: T;
  meta: MetaData;
}

export interface ApiCollectionResponse<T> {
  data: T[];
  meta: MetaData;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any> | null;
  request_id?: string;
}

export interface ApiErrorEnvelope {
  error: ApiError;
}

export interface NGO {
  id: string;
  name: string;
  external_id?: string | null;
  registration_number?: string | null;
}

export type ProjectSector =
  | "HEALTHCARE"
  | "EDUCATION"
  | "POVERTY_HUNGER"
  | "ENVIRONMENT"
  | "RURAL_DEVELOPMENT"
  | "GENDER_EQUALITY"
  | "LIVELIHOOD"
  | "DISASTER_RELIEF"
  | "SPORTS"
  | "ART_CULTURE"
  | "OTHER";

export type ProposalStatus =
  | "UPLOADED"
  | "EXTRACTING"
  | "EXTRACTED"
  | "VALIDATION_REQUIRED"
  | "READY"
  | "REJECTED"
  | "FAILED";

export type VerificationStatus =
  | "VERIFIED"
  | "PARTIALLY_VERIFIED"
  | "UNVERIFIED"
  | "MISSING"
  | "FLAGGED";

export type OptimizationStatus = "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";

export interface Geography {
  state: string;
  district: string;
  block?: string;
  pincode?: string;
}

export interface BeneficiaryProfile {
  target_group?: string;
  target_count: number;
  vulnerable_category?: string;
}

export interface Financials {
  requested_amount_paise: number;
  current_funding_paise: number;
  co_funding_amount_paise?: number;
  cost_per_beneficiary_paise?: number;
}

export interface ProposalDocument {
  document_id: string;
  proposal_id: string;
  filename: string;
  mime_type: string;
  file_size_bytes: number;
  sha256: string;
  created_at: string;
}

export interface Proposal {
  proposal_id: string;
  ngo_id: string;
  title: string;
  status: ProposalStatus;
  source_type: string;
  created_at: string;
  updated_at?: string | null;
}

export interface Project {
  project_id: string;
  proposal_id?: string | null;
  ngo_id: string;
  name: string;
  sector: ProjectSector;
  geographies: Geography[];
  beneficiary_profile?: BeneficiaryProfile | null;
  financials: Financials;
  duration_months: number;
  impact_metrics: Record<string, any>[];
  description?: string | null;
  schema_version: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ExtractionResult {
  proposal_id: string;
  status: ProposalStatus;
  project_id?: string | null;
  extraction_confidence: number;
  missing_fields: string[];
}

export interface ImpactDNA {
  dna_id: string;
  project_id: string;
  need_score: number;
  expected_impact_score: number;
  cost_efficiency_score: number;
  evidence_strength_score: number;
  scalability_score: number;
  implementation_risk_score: number;
  beneficiary_reach: number;
  estimated_impact_per_lakh: number;
  missing_fields: string[];
  extraction_confidence: number;
  model_name: string;
  prompt_version: string;
}

export interface OptimizationWeights {
  need: number;
  marginal_impact: number;
  cost_efficiency: number;
  evidence: number;
  scalability: number;
  equity: number;
  risk_penalty: number;
}

export interface OptimizationConstraints {
  max_allocation_per_project_paise?: number | null;
  max_allocation_per_region_paise?: number | null;
  minimum_allocation_per_project_paise?: number | null;
  require_full_budget_allocation?: boolean;
  regional_equity_enabled?: boolean;
}

export interface OptimizationRequest {
  budget_paise: number;
  project_ids: string[];
  weights: OptimizationWeights;
  constraints: OptimizationConstraints;
  marginal_increment_paise?: number;
}

export interface Allocation {
  allocation_id?: string;
  project_id: string;
  project_name?: string;
  state: string;
  sector?: string;
  requested_amount_paise?: number;
  allocated_amount_paise: number;
  status: string;
  base_score: number;
  saturation_index: number;
  marginal_impact_score: number;
  reason_codes: string[];
}

export interface OptimizationResult {
  run_id: string;
  status: OptimizationStatus;
  budget_paise: number;
  allocated_paise: number;
  unallocated_paise: number;
  allocations: Allocation[];
  total_predicted_impact: number;
  average_saturation: number;
  underserved_region_allocation_share: number;
  weights: OptimizationWeights;
  constraints: OptimizationConstraints;
  calculation_versions: Record<string, string>;
  created_at: string;
}

export interface ProjectPerformanceUpdate {
  project_id: string;
  actual_beneficiaries?: number | null;
  actual_spend_paise?: number | null;
  progress_percent?: number | null;
  updated_risk_score?: number | null;
  updated_impact_score?: number | null;
}

export interface ReallocationRequest {
  previous_run_id: string;
  budget_paise: number;
  performance_updates: ProjectPerformanceUpdate[];
  weights: OptimizationWeights;
  constraints: OptimizationConstraints;
}

export interface ReallocationResult {
  run_id: string;
  previous_run_id: string;
  old_allocations: Allocation[];
  new_allocations: Allocation[];
  changed_projects: string[];
  total_budget_shifted_paise: number;
  explanation: string[];
  calculation_versions: Record<string, string>;
  created_at: string;
}

export interface DueDiligenceCheck {
  check_name: string;
  status: VerificationStatus;
  source?: string | null;
  evidence?: string | null;
  confidence: number;
  checked_at: string;
}

export interface DueDiligenceReport {
  report_id: string;
  ngo_id: string;
  overall_status: VerificationStatus;
  risk_level: string;
  checks: DueDiligenceCheck[];
  flags: string[];
  missing_documents: string[];
  model_name?: string | null;
  model_version: string;
  disclaimer: string;
}

export interface AuditEvent {
  public_id: string;
  event_type: string;
  actor_id?: string | null;
  entity_type: string;
  entity_id?: string | null;
  request_id: string;
  run_id?: string | null;
  payload: Record<string, any>;
  created_at: string;
}
