import type {
  AuditEvent,
  BenchmarkMetrics,
  DisputeCase,
  DraftSentence,
  HealthResponse,
  QueueItem,
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthResponse>(res);
  },

  async seedCases(): Promise<{ cases_created: number; message: string }> {
    const res = await fetch(`${API_BASE}/seed`, { method: 'POST' });
    return handleResponse(res);
  },

  async getCases(statusFilter?: string): Promise<{ cases: DisputeCase[]; total: number }> {
    const url = statusFilter ? `${API_BASE}/cases?status=${statusFilter}` : `${API_BASE}/cases`;
    const res = await fetch(url);
    return handleResponse(res);
  },

  async getCase(id: string): Promise<DisputeCase> {
    const res = await fetch(`${API_BASE}/cases/${id}`);
    return handleResponse<DisputeCase>(res);
  },

  async getAudit(id: string): Promise<AuditEvent[]> {
    const res = await fetch(`${API_BASE}/cases/${id}/audit`);
    return handleResponse<AuditEvent[]>(res);
  },

  async analyzeCase(id: string): Promise<DisputeCase> {
    const res = await fetch(`${API_BASE}/cases/${id}/analyze`, { method: 'POST' });
    return handleResponse<DisputeCase>(res);
  },

  async draftCase(id: string): Promise<DisputeCase> {
    const res = await fetch(`${API_BASE}/cases/${id}/draft`, { method: 'POST' });
    return handleResponse<DisputeCase>(res);
  },

  async redteamCase(id: string): Promise<DisputeCase> {
    const res = await fetch(`${API_BASE}/cases/${id}/redteam`, { method: 'POST' });
    return handleResponse<DisputeCase>(res);
  },

  async updateDraft(id: string, draft: DraftSentence[]): Promise<DisputeCase> {
    const res = await fetch(`${API_BASE}/cases/${id}/draft`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ draft }),
    });
    return handleResponse<DisputeCase>(res);
  },

  async approveCase(id: string, approvedBy: string, confirm: boolean): Promise<DisputeCase> {
    const res = await fetch(`${API_BASE}/cases/${id}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved_by: approvedBy, confirm }),
    });
    return handleResponse<DisputeCase>(res);
  },

  async getQueue(): Promise<QueueItem[]> {
    const res = await fetch(`${API_BASE}/queue`);
    return handleResponse<QueueItem[]>(res);
  },

  async getBenchmark(useAll = false): Promise<BenchmarkMetrics> {
    const res = await fetch(`${API_BASE}/benchmark?use_all=${useAll}`);
    return handleResponse<BenchmarkMetrics>(res);
  },
};
