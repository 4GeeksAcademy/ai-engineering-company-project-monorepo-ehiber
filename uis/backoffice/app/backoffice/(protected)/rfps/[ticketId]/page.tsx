"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  approveRfpIntake,
  getRfpTicket,
  type DepartmentSection,
  type RfpTicketDetail,
} from "@/lib/rfp-api";

const ACTIVE_STATUSES = new Set([
  "analizando",
  "generando_borrador",
  "en_evaluación",
]);

function EvalBlock({ section }: { section: DepartmentSection }) {
  const evals = section.evaluation_results || {};
  const stage = typeof evals.stage === "string" ? evals.stage : null;
  const overall =
    typeof evals.overall_passed === "boolean" ? evals.overall_passed : null;

  const axes = ["readability", "pertinence", "compliance"] as const;

  return (
    <div style={{ marginTop: "0.75rem" }}>
      <p>
        Estado sección: <strong>{section.approval_status}</strong>
        {stage ? ` · stage ${stage}` : ""}
        {section.iteration_count ? ` · iter ${section.iteration_count}` : ""}
        {overall === true ? " · evaluación OK" : null}
        {overall === false ? " · evaluación con fallos" : null}
      </p>
      {axes.map((axis) => {
        const raw = evals[axis];
        if (!raw || typeof raw !== "object") return null;
        const block = raw as {
          passed?: boolean;
          reasons?: string[];
          score?: number | null;
        };
        return (
          <div key={axis} style={{ marginBottom: "0.5rem" }}>
            <strong>
              {axis}: {block.passed ? "pass" : "fail"}
              {typeof block.score === "number" ? ` (${block.score})` : ""}
            </strong>
            <ul>
              {(block.reasons || []).map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        );
      })}
      {section.draft_content ? (
        <details>
          <summary>Borrador generado</summary>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
            {section.draft_content}
          </pre>
        </details>
      ) : null}
    </div>
  );
}

export default function RfpTicketDetailPage() {
  const params = useParams<{ ticketId: string }>();
  const ticketId = params.ticketId;
  const [ticket, setTicket] = useState<RfpTicketDetail | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!ticketId) return;
    try {
      const data = await getRfpTicket(ticketId);
      setTicket(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el ticket.");
    }
  }, [ticketId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!ticket || !ACTIVE_STATUSES.has(ticket.status)) return;
    const id = window.setInterval(() => {
      void refresh();
    }, 2500);
    return () => window.clearInterval(id);
  }, [ticket, refresh]);

  const handleApprove = async () => {
    if (!ticketId) return;
    setBusy(true);
    setError("");
    try {
      await approveRfpIntake(ticketId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo aprobar el intake.");
    } finally {
      setBusy(false);
    }
  };

  if (!ticket && !error) {
    return (
      <div className="page-stack">
        <p>Cargando ticket…</p>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <p className="kicker">
          <Link href="/backoffice/rfps">← RFP Intake</Link>
        </p>
        <h1>{ticket?.client_name || ticket?.original_filename || "Ticket"}</h1>
        <p>
          Estado: <strong>{ticket?.status}</strong>
          {ticket?.approval_phase ? ` · fase ${ticket.approval_phase}` : ""}
        </p>
      </header>

      {error ? <p className="form-error">{error}</p> : null}

      {ticket?.status === "esperando_aprobación" &&
      ticket.approval_phase === "intake" ? (
        <section className="card-reveal form-grid">
          <p>
            Sales puede confirmar el routing antes de generar borradores (Parte
            2).
          </p>
          <button type="button" disabled={busy} onClick={() => void handleApprove()}>
            {busy ? "Confirmando…" : "Confirmar intake y generar borradores"}
          </button>
        </section>
      ) : null}

      {ticket?.approval_phase === "section_signoff" ? (
        <section className="card-reveal">
          <h2>Handoff Parte 3</h2>
          <p>
            Borradores y evaluaciones listos por departamento. La aprobación
            humana independiente llega en la Parte 3.
          </p>
        </section>
      ) : null}

      {ticket?.classifier_reason ? (
        <section className="card-reveal">
          <h2>Clasificador</h2>
          <p>
            {ticket.is_rfp ? "RFP válida" : "No es RFP"} — {ticket.classifier_reason}
          </p>
        </section>
      ) : null}

      {ticket?.error_message ? (
        <section className="card-reveal">
          <h2>Error</h2>
          <p className="form-error">{ticket.error_message}</p>
        </section>
      ) : null}

      <section className="card-reveal">
        <h2>Metadatos</h2>
        <ul>
          <li>País: {ticket?.client_country || "—"}</li>
          <li>Servicios: {(ticket?.services_requested || []).join(", ") || "—"}</li>
          <li>Volumen: {ticket?.monthly_volume ?? "—"}</li>
          <li>Deadline: {ticket?.deadline || "—"}</li>
          <li>
            Departamentos: {(ticket?.departments_needed || []).join(", ") || "—"}
          </li>
        </ul>
      </section>

      <section className="card-reveal">
        <h2>Por departamento</h2>
        {(ticket?.sections || []).length === 0 ? (
          <p>Sin secciones (documento descartado o aún analizando).</p>
        ) : (
          (ticket?.sections || []).map((section) => (
            <article key={section.department_id} style={{ marginBottom: "1.5rem" }}>
              <h3>
                {section.department_id} · {section.approver}
              </h3>
              <ul>
                {section.key_aspects.map((aspect) => (
                  <li key={aspect}>{aspect}</li>
                ))}
              </ul>
              <EvalBlock section={section} />
            </article>
          ))
        )}
      </section>

      {ticket?.synthesis_brief ? (
        <section className="card-reveal">
          <h2>Brief para Sales (Parte 1)</h2>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
            {ticket.synthesis_brief}
          </pre>
        </section>
      ) : null}
    </div>
  );
}
