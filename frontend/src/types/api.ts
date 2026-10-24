export type CaseStatus =
  | 'SUBMITTED'
  | 'PARSED'
  | 'INVESTIGATING'
  | 'READY_FOR_REVIEW'
  | 'PENDING_DOCUMENTS'
  | 'ESCALATED'
  | 'RESOLVED'
  | 'ERROR';

export type RecommendationOutcome = 'PASS' | 'MANUAL_REVIEW' | 'BLOCK';

export type CheckStatus =
  | 'MATCH'
  | 'POSSIBLE_MATCH'
  | 'MISMATCH'
  | 'NOT_FOUND'
  | 'UNAVAILABLE'
  | 'STALE_OR_UNCLEAR'
  | 'NOT_APPLICABLE';

export type SourceMode =
  | 'LIVE'
  | 'SIMULATED'
  | 'UNAVAILABLE'
  | 'MANUAL'
  | 'API'
  | 'DEMO'
  | 'QR'
  | 'LLM'
  | 'REGEX';

export type ReviewActionType =
  | 'APPROVE'
  | 'APPROVE_WITH_EXCEPTION'
  | 'REQUEST_DOCUMENTS'
  | 'ESCALATE'
  | 'REJECT';

export type ExtractionStatus =
  | 'EXTRACTED'
  | 'EXTRACTED_QR'
  | 'EXTRACTED_LLM'
  | 'EXTRACTED_REGEX'
  | 'CALCULATED'
  | 'INFERRED'
  | 'MANUALLY_CORRECTED'
  | 'CONFLICT'
  | 'UNAVAILABLE';

export interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
  tax_rate?: number;
}

export interface TaxBreakdownItem {
  tax_type: string;
  rate_pct: number;
  taxable_amount: number;
  tax_amount: number;
  status: ExtractionStatus;
}

export interface FieldExtractionMeta {
  status: ExtractionStatus;
  confidence: number;
  source?: string;
  extracted_value?: any;
  source_text?: string;
  notes?: string;
}

export interface InvoiceClaim {
  invoice_number: string;
  invoice_date?: string;
  supplier_name: string;
  legal_name?: string;
  gstin?: string;
  billing_address?: string;
  place_of_supply?: string;
  discount_amount?: number;
  round_off?: number;
  taxable_amount: number;
  cgst: number;
  sgst: number;
  igst: number;
  total_amount: number;
  tax_breakdown?: TaxBreakdownItem[];
  bank_account_masked?: string;
  ifsc_code?: string;
  line_items?: LineItem[];
  gstin_format_valid?: boolean;
  arithmetic_valid?: boolean;
  arithmetic_notes?: string;
  raw_text?: string;
  extraction_metadata?: Record<string, FieldExtractionMeta>;
  parsing_errors?: string[];
  parsing_warnings?: string[];
  is_scanned_image?: boolean;
  ocr_applied?: boolean;
  ocr_status_message?: string;
  file_sha256?: string;
  duplicate_status?: string;
  duplicate_case_id?: string;
  buyer_gstin?: string;
  buyer_name?: string;
  irn?: string;
  qr_data?: Record<string, any>;
  qr_signature_status?: string;
  extraction_conflicts?: any[];
}

export interface EvidenceItem {
  evidence_id: string;
  source_url: string;
  source_name: string;
  claim_supported: string;
  source_type: string;
  source_mode?: SourceMode;
  is_fallback?: boolean;
  fallback_reason?: string;
  retrieved_at: string;
  raw_excerpt: string;
  facts: Record<string, any>;
  is_authoritative: boolean;
  match_rationale?: string;
}

export interface FieldCheckResult {
  check_id: string;
  field_name: string;
  invoice_value?: string;
  evidence_value?: string;
  status: CheckStatus;
  reason_code?: string;
  explanation: string;
  evidence_id?: string;
  source_url?: string;
  source_mode?: SourceMode;
  is_fallback?: boolean;
}

export interface RuleTrigger {
  rule_id: string;
  rule_name: string;
  severity: string;
  weight: number;
  is_hard_gate: boolean;
  description: string;
  reason_code: string;
  evidence_reference?: string;
  missing_evidence?: string;
}

export interface ForensicVectorScores {
  itc_clawback_risk_index: number;
  director_shell_contagion_score: number;
  address_collocation_density: number;
  operational_grounding_score: number;
  popup_velocity_factor: number;
}

export interface ITCExposureDetails {
  tax_amount_claimed: number;
  itc_clawback_probability: number;
  statutory_penalty_inr: number;
  estimated_interest_inr: number;
  total_financial_liability_inr: number;
  applicable_sections: string[];
  risk_tier: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW';
  cfo_advisory: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  risk_level: string;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  is_flagged: boolean;
  weight: number;
}

export interface EntityGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_flagged_edges: number;
}

export interface RiskAssessment {
  assessment_id: string;
  case_id: string;
  ruleset_version: string;
  recommendation: RecommendationOutcome;
  risk_score?: number;
  score_explanation?: string;
  reason_codes: string[];
  field_checks: FieldCheckResult[];
  hard_gates_triggered: string[];
  forensic_vectors?: ForensicVectorScores;
  itc_exposure?: ITCExposureDetails;
  entity_graph?: EntityGraph;
  triggered_rules?: RuleTrigger[];
  missing_evidence_items?: string[];
  evidence_completeness: string;
  evidence_provenance_mode?: SourceMode;
  human_signoff_required: boolean;
  assessed_at: string;
}

export interface ReviewSubmissionRequest {
  action: ReviewActionType;
  rationale: string;
  reviewer_id?: string;
  reviewer_role?: string;
  requested_documents?: string[];
}

export interface ReviewAction {
  action_id: string;
  case_id: string;
  reviewer_id: string;
  reviewer_role?: string;
  action: ReviewActionType;
  rationale: string;
  requested_documents: string[];
  auth_mode?: string;
  recorded_at: string;
}

export interface Case {
  case_id: string;
  case_reference: string;
  status: CaseStatus;
  source_mode: SourceMode;
  created_at: string;
  updated_at: string;
  created_by: string;
  file_sha256?: string;
  duplicate_of_case_id?: string;
  duplicate_type?: string;
  invoice?: InvoiceClaim;
  evidence_items: EvidenceItem[];
  assessment?: RiskAssessment;
  review?: ReviewAction;
  review_history?: ReviewAction[];
  audit_hash_sha256?: string;
}

export interface CaseSummary {
  case_id: string;
  case_reference: string;
  status: CaseStatus;
  source_mode?: SourceMode;
  supplier_name: string;
  invoice_number: string;
  total_amount: number;
  recommendation?: RecommendationOutcome;
  risk_score?: number;
  review_status?: string;
  gstin_claim?: string;
  duplicate_type?: string;
  created_at: string;
}

export interface InvoiceCorrection {
  corrected_supplier_name?: string;
  corrected_legal_name?: string;
  corrected_invoice_number?: string;
  corrected_invoice_date?: string;
  corrected_gstin?: string;
  corrected_taxable_amount?: number;
  corrected_cgst?: number;
  corrected_sgst?: number;
  corrected_igst?: number;
  corrected_total_amount?: number;
  corrected_bank_account?: string;
  corrected_ifsc_code?: string;
  correction_notes?: string;
  reviewer_id?: string;
}

export interface AuditEvent {
  event_id: string;
  case_id: string;
  event_type: string;
  actor: string;
  actor_role: string;
  timestamp: string;
  event_data: Record<string, any>;
  ruleset_version: string;
  prev_hash: string;
  event_hash: string;
}

export interface ManualGstinEvidenceRequest {
  gstin: string;
  legal_name: string;
  trade_name?: string;
  status: string;
  registration_date?: string;
  constitution_of_business?: string;
  taxpayer_type?: string;
  source_url?: string;
  notes?: string;
  reviewer_id?: string;
}

export interface ExplainVerdictResponse {
  case_id: string;
  verdict: string;
  risk_score: number;
  score_policy: string;
  why_this_verdict: string[];
  what_would_change_it: string[];
}

export interface AuditVerifyResponse {
  case_id: string;
  total_events: number;
  chain_valid: boolean;
  broken_event_id?: string | null;
  broken_event_index?: number | null;
  detail: string;
}
