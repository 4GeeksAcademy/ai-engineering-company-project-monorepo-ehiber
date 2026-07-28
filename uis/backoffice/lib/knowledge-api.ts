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

export type MemoryProposal = {
  proposal_id: string;
  content: string;
  consolidation_key: string;
  carrier?: string | null;
  country?: string | null;
  topic?: string | null;
  status: string;
};

export type MemoryDecision = {
  handled: boolean;
  decision?: string | null;
  proposal_id?: string | null;
  message?: string | null;
};

export type KnowledgeAskResponse = {
  answer: string;
  sources: KnowledgeSource[];
  run_id: string;
  trace: KnowledgeTraceStep[];
  checkpointed: boolean;
  memory_proposal?: MemoryProposal | null;
  memory_decision?: MemoryDecision | null;
};

export type AskKnowledgeInput = {
  question: string;
  memory_decision?: "approve" | "reject" | "edit";
  proposal_id?: string;
  edited_content?: string;
};

export async function askKnowledge(
  input: string | AskKnowledgeInput,
): Promise<KnowledgeAskResponse> {
  const token = getStoredToken();
  if (!token) {
    throw new Error("Debes iniciar sesión para usar el asistente de conocimiento.");
  }

  const payload: AskKnowledgeInput =
    typeof input === "string" ? { question: input } : input;

  const response = await fetch(`${apiBaseUrl}/api/knowledge/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(errorBody || "No se pudo obtener la respuesta del asistente.");
  }

  return response.json() as Promise<KnowledgeAskResponse>;
}
