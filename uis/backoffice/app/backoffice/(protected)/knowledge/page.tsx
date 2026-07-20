"use client";

import { FormEvent, useState } from "react";
import { askKnowledge, type KnowledgeAskResponse } from "@/lib/knowledge-api";

export default function KnowledgePage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<KnowledgeAskResponse | null>(null);

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

  return (
    <div className="page-stack">
      <header className="page-header">
        <p className="kicker">TrackFlow</p>
        <h1>Knowledge Assistant</h1>
        <p>
          Consulta políticas comerciales con respuestas generadas desde la base de
          conocimiento interna.
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

      {result ? (
        <section className="card-reveal page-stack">
          <div>
            <h2>Respuesta</h2>
            <p>{result.answer}</p>
            <p className="kicker">run_id: {result.run_id}</p>
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
                <li key={`${step.node}-${step.ms}`}>
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
