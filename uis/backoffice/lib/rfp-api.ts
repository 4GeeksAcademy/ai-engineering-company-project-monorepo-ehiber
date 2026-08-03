import { getStoredToken } from "@repo/shared/auth";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_TRACKFLOW_API_URL ?? "http://localhost:8000";

export type RfpTicketSummary = {
  ticket_id: string;
  rfp_id: string;
  status: string;
  original_filename: string;
  client_name?: string | null;
  client_country?: string | null;
  is_rfp?: boolean | null;
  departments_needed: string[];
  created_at: string;
  updated_at: string;
};

export type DepartmentSection = {
  department_id: string;
  key_aspects: string[];
  draft_content?: string | null;
  evaluation_results: Record<string, unknown>;
  approval_status: string;
  approver: string;
  approved_at?: string | null;
  iteration_count: number;
};

export type RfpTicketDetail = RfpTicketSummary & {
  approval_phase?: string | null;
  classifier_reason?: string | null;
  services_requested: string[];
  monthly_volume?: number | null;
  deadline?: string | null;
  budget_range?: string | null;
  readability_metrics: Record<string, unknown>;
  processing_cost_estimate: Record<string, unknown>;
  synthesis_brief?: string | null;
  markdown_preview?: string | null;
  error_message?: string | null;
  celery_task_id?: string | null;
  sections: DepartmentSection[];
};

function authHeaders(json = true): HeadersInit {
  const token = getStoredToken();
  if (!token) {
    throw new Error("Sesión no encontrada. Inicia sesión de nuevo.");
  }
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };
  if (json) {
    headers["Content-Type"] = "application/json";
  }
  return headers;
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    return JSON.stringify(data);
  } catch {
    return response.statusText || "Error de API";
  }
}

export async function listRfpTickets(): Promise<RfpTicketSummary[]> {
  const response = await fetch(`${apiBaseUrl}/api/rfp/tickets`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getRfpTicket(ticketId: string): Promise<RfpTicketDetail> {
  const response = await fetch(`${apiBaseUrl}/api/rfp/tickets/${ticketId}`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function uploadRfpPdf(file: File): Promise<{
  ticket_id: string;
  rfp_id: string;
  status: string;
}> {
  const token = getStoredToken();
  if (!token) {
    throw new Error("Sesión no encontrada. Inicia sesión de nuevo.");
  }
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${apiBaseUrl}/api/rfp/tickets`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body,
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function approveRfpIntake(ticketId: string): Promise<{
  ticket_id: string;
  status: string;
  message: string;
}> {
  const response = await fetch(
    `${apiBaseUrl}/api/rfp/tickets/${ticketId}/approve-intake`,
    {
      method: "POST",
      headers: authHeaders(),
    },
  );
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}
