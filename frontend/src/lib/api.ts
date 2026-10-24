import {
  Case,
  CaseSummary,
  ReviewAction,
  ReviewSubmissionRequest,
  InvoiceCorrection,
  AuditEvent
} from '../types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
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
      // Body is not JSON
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
  /**
   * Retrieves all vendor due-diligence cases.
   */
  async getCases(): Promise<CaseSummary[]> {
    const res = await fetch(`${API_BASE_URL}/cases`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      },
      cache: 'no-store'
    });
    return handleResponse<CaseSummary[]>(res);
  },

  /**
   * Retrieves details of a specific case by case_id.
   */
  async getCase(caseId: string): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      },
      cache: 'no-store'
    });
    return handleResponse<Case>(res);
  },

  /**
   * Creates a new case via raw FormData (used by intake upload form).
   */
  async createCase(formData: FormData): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json'
      },
      body: formData
    });
    return handleResponse<Case>(res);
  },

  /**
   * Uploads an invoice document (PDF/Image) for parsing and case creation.
   */
  async uploadInvoice(
    file: File,
    metadata?: { supplier_name?: string; invoice_number?: string; total_amount?: number }
  ): Promise<Case> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata?.supplier_name) formData.append('supplier_name', metadata.supplier_name);
    if (metadata?.invoice_number) formData.append('invoice_number', metadata.invoice_number);
    if (metadata?.total_amount !== undefined) formData.append('total_amount', String(metadata.total_amount));

    return this.createCase(formData);
  },

  /**
   * Triggers autonomous 4-hop TinyFish forensic investigation on a case.
   */
  async triggerInvestigation(caseId: string): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/investigate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    return handleResponse<Case>(res);
  },

  /**
   * Submits human reviewer sign-off decision with mandatory rationale.
   * Client provides intent; server generates trusted action_id and timestamps.
   */
  async submitReview(
    caseId: string,
    review: ReviewSubmissionRequest
  ): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/review`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Reviewer-Token': 'vendorshield-dev-review-token-2026'
      },
      body: JSON.stringify({
        reviewer_id: review.reviewer_id || 'analyst',
        reviewer_role: review.reviewer_role || 'ap_analyst',
        action: review.action,
        rationale: review.rationale,
        requested_documents: review.requested_documents || []
      })
    });
    return handleResponse<Case>(res);
  },

  /**
   * Corrects extracted invoice claims and triggers automatic re-assessment.
   */
  async correctInvoice(caseId: string, correction: InvoiceCorrection): Promise<Case> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/correct`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(correction)
    });
    return handleResponse<Case>(res);
  },

  /**
   * Retrieves the cryptographically chained audit trail for a case.
   */
  async getAuditTrail(caseId: string): Promise<AuditEvent[]> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/audit-trail`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      },
      cache: 'no-store'
    });
    return handleResponse<AuditEvent[]>(res);
  },

  /**
   * Downloads the human-readable Markdown due-diligence audit report.
   */
  async downloadReport(caseId: string): Promise<string> {
    const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/report`, {
      method: 'GET',
      headers: {
        'Accept': 'text/plain'
      }
    });
    if (!res.ok) {
      throw new Error(`Failed to download report (status ${res.status})`);
    }
    return res.text();
  },

  /**
   * Alias for downloadReport.
   */
  async getAuditReport(caseId: string): Promise<string> {
    return this.downloadReport(caseId);
  }
};
