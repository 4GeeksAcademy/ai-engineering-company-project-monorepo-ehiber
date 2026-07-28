import { getStoredToken } from "@repo/shared/auth";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_TRACKFLOW_API_URL ?? "http://localhost:8000";

export type KnowledgeSource = {
  source_document: string;
  section: string;
};

export type KnowledgeTraceStep = {
  node: string;
  status: string;
  ms: number;
  detail: Record<string, unknown>;
};

export type KnowledgeAskResponse = {
  answer: string;
  sources: KnowledgeSource[];
  run_id: string;
  trace: KnowledgeTraceStep[];
  checkpointed: boolean;
};

export async function askKnowledge(question: string): Promise<KnowledgeAskResponse> {
  const token = getStoredToken();
  if (!token) {
    throw new Error("Debes iniciar sesión para usar el asistente de conocimiento.");
  }

  const response = await fetch(`${apiBaseUrl}/api/knowledge/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(errorBody || "No se pudo obtener la respuesta del asistente.");
  }

  return response.json() as Promise<KnowledgeAskResponse>;
}
