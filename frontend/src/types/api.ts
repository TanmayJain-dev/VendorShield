export type CaseStatus =
  | 'SUBMITTED'
  | 'PARSED'
  | 'INVESTIGATING'
  | 'READY_FOR_REVIEW'
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

export type SourceMode = 'LIVE' | 'SIMULATED';

export type ReviewActionType =
  | 'APPROVE'
  | 'APPROVE_WITH_EXCEPTION'
  | 'REQUEST_DOCUMENTS'
  | 'ESCALATE'
  | 'REJECT';

export interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface InvoiceClaim {
  invoice_number: string;
  invoice_date?: string;
  supplier_name: string;
  legal_name?: string;
  gstin?: string;
  billing_address?: string;
  taxable_amount: number;
  cgst: number;
  sgst: number;
  igst: number;
  total_amount: number;
  bank_account_masked?: string;
  ifsc_code?: string;
  line_items?: LineItem[];
  gstin_format_valid?: boolean;
  arithmetic_valid?: boolean;
  raw_text?: string;
}

export interface EvidenceItem {
  evidence_id: string;
  source_url: string;
  source_name: string;
  claim_supported: string;
  source_type: string;
  retrieved_at: string;
  raw_excerpt: string;
  facts: Record<string, any>;
  is_authoritative: boolean;
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
}

export interface RiskAssessment {
  assessment_id: string;
  case_id: string;
  ruleset_version: string;
  recommendation: RecommendationOutcome;
  risk_score?: number;
  reason_codes: string[];
  field_checks: FieldCheckResult[];
  hard_gates_triggered: string[];
  evidence_completeness: string;
  human_signoff_required: boolean;
  assessed_at: string;
}

export interface ReviewAction {
  action_id: string;
  case_id: string;
  reviewer_id: string;
  action: ReviewActionType;
  rationale: string;
  requested_documents: string[];
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
  invoice?: InvoiceClaim;
  evidence_items: EvidenceItem[];
  assessment?: RiskAssessment;
  review?: ReviewAction;
  audit_hash_sha256?: string;
}

export interface CaseSummary {
  case_id: string;
  case_reference: string;
  status: CaseStatus;
  supplier_name: string;
  invoice_number: string;
  total_amount: number;
  recommendation?: RecommendationOutcome;
  risk_score?: number;
  review_status?: string;
  gstin_claim?: string;
  created_at: string;
}

export interface InvoiceCorrection {
  corrected_supplier_name?: string;
  corrected_gstin?: string;
  corrected_total_amount?: number;
  correction_notes?: string;
}

