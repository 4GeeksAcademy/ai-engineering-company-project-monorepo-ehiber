import { getStoredToken } from "@repo/shared/auth";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_TRACKFLOW_API_URL ?? "http://localhost:8000";

export type KnowledgeSource = {
  source_document: string;
  section: string;
};

export type KnowledgeAskResponse = {
  answer: string;
  sources: KnowledgeSource[];
};

export async function askKnowledge(question: string): Promise<KnowledgeAskResponse> {
  const token = getStoredToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${apiBaseUrl}/api/knowledge/ask`, {
    method: "POST",
    headers,
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(errorBody || "No se pudo obtener la respuesta del asistente.");
  }

  return response.json() as Promise<KnowledgeAskResponse>;
}
