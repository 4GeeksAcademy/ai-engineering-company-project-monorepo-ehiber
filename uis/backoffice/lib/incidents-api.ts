import { authClient } from "@/lib/auth";
import type {
  Incident,
  IncidentBranch,
  IncidentCategory,
  IncidentCreate,
  IncidentOrigin,
  IncidentStatus,
  IncidentSummary,
} from "@/lib/incidents-types";

type ListIncidentFilters = {
  status?: IncidentStatus;
  origin?: IncidentOrigin;
  branch?: IncidentBranch;
  category?: IncidentCategory;
};

export const incidentsApi = {
  list: async (filters: ListIncidentFilters = {}): Promise<Incident[]> => {
    const query = new URLSearchParams();

    if (filters.status) {
      query.set("status", filters.status);
    }
    if (filters.origin) {
      query.set("origin", filters.origin);
    }
    if (filters.branch) {
      query.set("branch", filters.branch);
    }
    if (filters.category) {
      query.set("category", filters.category);
    }

    const suffix = query.toString() ? `?${query.toString()}` : "";
    return authClient.authFetch<Incident[]>(`/api/incidents${suffix}`);
  },

  summary: async (): Promise<IncidentSummary> => {
    return authClient.authFetch<IncidentSummary>("/api/incidents/summary");
  },

  create: async (payload: IncidentCreate): Promise<Incident> => {
    return authClient.authFetch<Incident>("/api/incidents", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateStatus: async (incidentId: number, status: IncidentStatus): Promise<Incident> => {
    return authClient.authFetch<Incident>(`/api/incidents/${incidentId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },
};
