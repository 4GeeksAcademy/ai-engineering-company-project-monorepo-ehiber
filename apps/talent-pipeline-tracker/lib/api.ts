import type {
  CandidateListFilters,
  CandidateListResponse,
  CandidateNote,
  CandidateNotesResponse,
  CandidateRecord,
  CandidateRecordCreate,
  CandidateRecordPatch,
} from "@/types/tracker";

const getApiBaseUrl = (): string => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL;

  if (!apiBaseUrl) {
    throw new Error(
      "NEXT_PUBLIC_API_URL no esta configurada. Revisa tu archivo .env.local o .env.example.",
    );
  }

  return apiBaseUrl.replace(/\/$/, "");
};

const getErrorMessage = async (response: Response): Promise<string> => {
  try {
    const payload = (await response.json()) as {
      error?: string;
      detail?: string | Record<string, string>;
    };

    if (typeof payload.detail === "string") {
      return payload.detail;
    }

    if (payload.detail && typeof payload.detail === "object") {
      return Object.values(payload.detail).join(". ");
    }

    if (payload.error) {
      return payload.error;
    }
  } catch {
    return `La API respondio con estado ${response.status}.`;
  }

  return `La API respondio con estado ${response.status}.`;
};

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
};

export const trackerApi = {
  getRecords: async (
    filters: CandidateListFilters = {},
  ): Promise<CandidateListResponse> => {
    const params = new URLSearchParams();

    if (filters.status) {
      params.set("status", filters.status);
    }
    if (filters.stage) {
      params.set("stage", filters.stage);
    }
    if (filters.search) {
      params.set("search", filters.search);
    }
    if (filters.page) {
      params.set("page", String(filters.page));
    }
    params.set("limit", "12");

    const suffix = params.toString() ? `?${params.toString()}` : "";

    return request<CandidateListResponse>(`/records${suffix}`);
  },

  getRecordById: async (candidateId: string): Promise<CandidateRecord> => {
    return request<CandidateRecord>(`/records/${candidateId}`);
  },

  createRecord: async (payload: CandidateRecordCreate): Promise<CandidateRecord> => {
    return request<CandidateRecord>("/records", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateRecord: async (
    candidateId: string,
    payload: CandidateRecordCreate,
  ): Promise<CandidateRecord> => {
    return request<CandidateRecord>(`/records/${candidateId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  patchRecord: async (
    candidateId: string,
    payload: CandidateRecordPatch,
  ): Promise<CandidateRecord> => {
    return request<CandidateRecord>(`/records/${candidateId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  getNotes: async (candidateId: string): Promise<CandidateNotesResponse> => {
    return request<CandidateNotesResponse>(`/records/${candidateId}/notes`);
  },

  createNote: async (
    candidateId: string,
    content: string,
  ): Promise<CandidateNote> => {
    return request<CandidateNote>(`/records/${candidateId}/notes`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  },

  deleteNote: async (candidateId: string, noteId: string): Promise<void> => {
    return request<void>(`/records/${candidateId}/notes/${noteId}`, {
      method: "DELETE",
    });
  },
};
