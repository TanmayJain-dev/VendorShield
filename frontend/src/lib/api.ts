import {
  Case,
  CaseSummary,
  ReviewAction,
  ReviewSubmissionRequest,
  InvoiceCorrection,
  AuditEvent,
  ManualGstinEvidenceRequest,
  ExplainVerdictResponse,
  AuditVerifyResponse,
  Gstr2bImportResponse,
  Gstr2bEntry
} from '../types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    ...extraHeaders
  };
  if (typeof window !== 'undefined') {
    const token = sessionStorage.getItem('vendorshield_token') || 'dev-reviewer-token';
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      headers['X-Reviewer-Token'] = token;
    }
  } else {
    headers['Authorization'] = 'Bearer dev-reviewer-token';
    headers['X-Reviewer-Token'] = 'dev-reviewer-token';
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    if (res.status === 401 && typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('vendorshield_auth_error'));
    }
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      if (typeof data.detail === 'string') {
        errorDetail = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorDetail = data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
      } else if (data.message) {
        errorDetail = data.message;
      }
    } catch {
      try {
        const text = await res.text();
        if (text) errorDetail = text;
      } catch {
        // ignore
      }
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getCaseFileUrl(caseId: string): string {
    return `${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/file`;
  },

  async getCases(includeDemo = true): Promise<CaseSummary[]> {
    const res = await fetch(`${API_BASE_URL}/cases?include_demo=${includeDemo}`, {
      method: 'GET',
      headers: getAuthHeaders(),
      cache: 'no-store'
    });
    return handleResponse<CaseSummary[]>(res);
  },

  async getCase(caseId: string): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}`, {
      method: 'GET',
      headers: getAuthHeaders(),
      cache: 'no-store'
    });
    return handleResponse<Case>(res);
  },

  async createCase(formData: FormData): Promise<Case> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (typeof window !== 'undefined') {
      const token = sessionStorage.getItem('vendorshield_token') || 'dev-reviewer-token';
      if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE_URL}/cases`, {
      method: 'POST',
      headers,
      body: formData
    });
    return handleResponse<Case>(res);
  },

  async uploadInvoice(
    file: File,
    metadata?: { supplier_name?: string; invoice_number?: string; total_amount?: number; is_demo?: boolean }
  ): Promise<Case> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata?.supplier_name) formData.append('supplier_name', metadata.supplier_name);
    if (metadata?.invoice_number) formData.append('invoice_number', metadata.invoice_number);
    if (metadata?.total_amount !== undefined) formData.append('total_amount', String(metadata.total_amount));
    if (metadata?.is_demo !== undefined) formData.append('is_demo', String(metadata.is_demo));

    return this.createCase(formData);
  },

  async triggerInvestigation(caseId: string): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/investigate`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' })
    });
    return handleResponse<Case>(res);
  },

  async submitReview(
    caseId: string,
    review: ReviewSubmissionRequest
  ): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/review`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        reviewer_id: review.reviewer_id || 'reviewer',
        reviewer_role: review.reviewer_role || 'reviewer',
        action: review.action,
        rationale: review.rationale,
        requested_documents: review.requested_documents || []
      })
    });
    return handleResponse<Case>(res);
  },

  async correctInvoice(caseId: string, correction: InvoiceCorrection): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/correct`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(correction)
    });
    return handleResponse<Case>(res);
  },

  async submitManualGstinEvidence(caseId: string, payload: ManualGstinEvidenceRequest): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/evidence/gstin`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload)
    });
    return handleResponse<Case>(res);
  },

  async explainVerdict(caseId: string): Promise<ExplainVerdictResponse> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/explain`, {
      method: 'GET',
      headers: getAuthHeaders(),
      cache: 'no-store'
    });
    return handleResponse<ExplainVerdictResponse>(res);
  },

  async getAuditTrail(caseId: string): Promise<AuditEvent[]> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/audit-trail`, {
      method: 'GET',
      headers: getAuthHeaders(),
      cache: 'no-store'
    });
    return handleResponse<AuditEvent[]>(res);
  },

  async verifyAuditChain(caseId: string): Promise<AuditVerifyResponse> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/audit/verify`, {
      method: 'GET',
      headers: getAuthHeaders(),
      cache: 'no-store'
    });
    return handleResponse<AuditVerifyResponse>(res);
  },

  async downloadReport(caseId: string): Promise<string> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/report`, {
      method: 'GET',
      headers: getAuthHeaders({ 'Accept': 'text/plain' })
    });
    if (!res.ok) {
      throw new Error(`Failed to download report (status ${res.status})`);
    }
    return res.text();
  },

  async getAuditReport(caseId: string): Promise<string> {
    return this.downloadReport(caseId);
  },
  async importGstr2b(file: File): Promise<Gstr2bImportResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (typeof window !== 'undefined') {
      const token = sessionStorage.getItem('vendorshield_token') || 'dev-reviewer-token';
      if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE_URL}/gstr2b/import`, {
      method: 'POST',
      headers,
      body: formData
    });
    return handleResponse<Gstr2bImportResponse>(res);
  },

  async getUnmatchedGstr2b(): Promise<Gstr2bEntry[]> {
    const res = await fetch(`${API_BASE_URL}/gstr2b/unmatched`, {
      method: 'GET',
      headers: getAuthHeaders(),
      cache: 'no-store'
    });
    return handleResponse<Gstr2bEntry[]>(res);
  },

  async getGstr2bMatch(caseId: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/gstr2b/match/${encodeURIComponent(caseId)}`, {
      method: 'GET',
      headers: getAuthHeaders(),
      cache: 'no-store'
    });
    return handleResponse<any>(res);
  }
};
