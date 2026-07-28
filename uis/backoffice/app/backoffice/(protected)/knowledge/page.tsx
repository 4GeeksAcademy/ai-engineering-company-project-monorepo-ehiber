"use client";

import { FormEvent, useState } from "react";
import {
  askKnowledge,
  type KnowledgeAskResponse,
  type MemoryProposal,
} from "@/lib/knowledge-api";

export default function KnowledgePage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<KnowledgeAskResponse | null>(null);
  const [pendingProposal, setPendingProposal] = useState<MemoryProposal | null>(null);
  const [editText, setEditText] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length < 3) {
      setError("Escribe una pregunta de al menos 3 caracteres.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await askKnowledge(trimmed);
      setResult(response);
      if (response.memory_proposal) {
        setPendingProposal(response.memory_proposal);
        setEditText(response.memory_proposal.content);
      }
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "No se pudo consultar la base de conocimiento.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleMemoryDecision = async (
    decision: "approve" | "reject" | "edit",
  ) => {
    if (!pendingProposal) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await askKnowledge({
        question:
          decision === "approve"
            ? "Sí, guarda esa memoria."
            : decision === "reject"
              ? "No, no lo guardes."
              : "Guarda esto en su lugar.",
        memory_decision: decision,
        proposal_id: pendingProposal.proposal_id,
        edited_content: decision === "edit" ? editText : undefined,
      });
      setResult(response);
      setPendingProposal(null);
      setEditText("");
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "No se pudo resolver la propuesta de memoria.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-stack">
      <header className="page-header">
        <p className="kicker">TrackFlow</p>
        <h1>Knowledge Assistant</h1>
        <p>
          Asistente CX con guardrails y memoria consentida: solo guarda lo que
          apruebes explícitamente.
        </p>
      </header>

      <form className="card-reveal form-grid" onSubmit={handleSubmit}>
        <label htmlFor="knowledge-question">Pregunta</label>
        <textarea
          id="knowledge-question"
          rows={4}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ej. ¿Cuál es la ventana de devolución estándar?"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Consultando..." : "Preguntar"}
        </button>
      </form>

      {error ? <p className="form-error">{error}</p> : null}

      {pendingProposal ? (
        <section className="card-reveal page-stack">
          <h2>Propuesta de memoria</h2>
          <p>
            Detecté algo útil para futuras consultas CX. ¿Quieres que lo
            recuerde?
          </p>
          <p>
            <strong>{pendingProposal.content}</strong>
          </p>
          <p className="kicker">
            key: {pendingProposal.consolidation_key} · id:{" "}
            {pendingProposal.proposal_id}
          </p>
          <label htmlFor="memory-edit">Editar antes de guardar (opcional)</label>
          <textarea
            id="memory-edit"
            rows={3}
            value={editText}
            onChange={(event) => setEditText(event.target.value)}
          />
          <div className="form-grid" style={{ gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem" }}>
            <button type="button" disabled={loading} onClick={() => handleMemoryDecision("approve")}>
              Sí, recordar
            </button>
            <button type="button" disabled={loading} onClick={() => handleMemoryDecision("edit")}>
              Guardar editado
            </button>
            <button type="button" disabled={loading} onClick={() => handleMemoryDecision("reject")}>
              No guardar
            </button>
          </div>
        </section>
      ) : null}

      {result ? (
        <section className="card-reveal page-stack">
          <div>
            <h2>Respuesta</h2>
            <p style={{ whiteSpace: "pre-wrap" }}>{result.answer}</p>
            <p className="kicker">run_id: {result.run_id}</p>
            {result.memory_decision?.handled ? (
              <p className="kicker">
                Memoria: {result.memory_decision.decision} —{" "}
                {result.memory_decision.message}
              </p>
            ) : null}
          </div>
          <div>
            <h3>Fuentes</h3>
            {result.sources.length > 0 ? (
              <ul>
                {result.sources.map((source) => (
                  <li key={`${source.source_document}-${source.section}`}>
                    {source.source_document} — {source.section}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No se recuperaron fuentes para esta consulta.</p>
            )}
          </div>
          <div>
            <h3>Trace</h3>
            <ul>
              {result.trace.map((step) => (
                <li key={`${step.node}-${step.ms}-${step.status}`}>
                  {step.node} ({step.status}, {step.ms}ms)
                </li>
              ))}
            </ul>
          </div>
        </section>
      ) : null}
    </div>
  );
}
