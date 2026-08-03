"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  approveRfpIntake,
  approveSection,
  arbitrateSection,
  getRfpTicket,
  rejectSection,
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
        {section.iteration_count ? ` · gen-iter ${section.iteration_count}` : ""}
        {section.human_approval_rounds
          ? ` · human-rounds ${section.human_approval_rounds}`
          : ""}
        {overall === true ? " · eval OK" : null}
        {overall === false ? " · eval con fallos" : null}
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
  const [comment, setComment] = useState("");

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

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await fn();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Operación fallida.");
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

  const approvedCount = (ticket?.sections || []).filter(
    (s) => s.approval_status === "approved",
  ).length;
  const totalSections = (ticket?.sections || []).length;

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
          {totalSections > 0
            ? ` · firmas ${approvedCount}/${totalSections}`
            : ""}
        </p>
      </header>

      {error ? <p className="form-error">{error}</p> : null}

      {ticket?.status === "esperando_aprobación" &&
      ticket.approval_phase === "intake" ? (
        <section className="card-reveal form-grid">
          <p>Confirmar routing (Parte 1) para generar borradores y abrir HITL.</p>
          <button
            type="button"
            disabled={busy}
            onClick={() => void run(() => approveRfpIntake(ticketId))}
          >
            {busy ? "Confirmando…" : "Confirmar intake y continuar"}
          </button>
        </section>
      ) : null}

      {ticket?.approval_phase === "section_signoff" ? (
        <section className="card-reveal form-grid">
          <h2>Aprobación humana (Parte 3)</h2>
          <p>
            Cada departamento firma de forma independiente. Un dept en espera no
            bloquea a los demás.
          </p>
          <label htmlFor="decision-comment">Comentario (opcional)</label>
          <input
            id="decision-comment"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Motivo de rechazo / nota"
          />
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
          <p>Sin secciones.</p>
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
              {ticket?.approval_phase === "section_signoff" &&
              section.approval_status !== "approved" ? (
                <div className="form-grid" style={{ marginTop: "0.75rem" }}>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void run(() =>
                        approveSection(ticketId, section.department_id, comment),
                      )
                    }
                  >
                    Aprobar
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void run(() =>
                        rejectSection(ticketId, section.department_id, comment),
                      )
                    }
                  >
                    Rechazar
                  </button>
                  {section.approval_status === "needs_arbitration" ||
                  (section.human_approval_rounds || 0) >= 2 ? (
                    <>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() =>
                          void run(() =>
                            arbitrateSection(
                              ticketId,
                              section.department_id,
                              "force_approve",
                              comment,
                            ),
                          )
                        }
                      >
                        Arbitrar: forzar approve
                      </button>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() =>
                          void run(() =>
                            arbitrateSection(
                              ticketId,
                              section.department_id,
                              "force_reject",
                              comment,
                            ),
                          )
                        }
                      >
                        Arbitrar: rechazar
                      </button>
                    </>
                  ) : null}
                </div>
              ) : null}
            </article>
          ))
        )}
      </section>

      {ticket?.final_document ? (
        <section className="card-reveal">
          <h2>Documento final</h2>
          <p>
            Moneda: {ticket.final_document.currency} · Generado:{" "}
            {ticket.final_document.generated_at}
          </p>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
            {ticket.final_document.content}
          </pre>
        </section>
      ) : null}

      {(ticket?.run_trace || []).length > 0 ? (
        <section className="card-reveal">
          <h2>Trace (agent / input / output / timestamp)</h2>
          <ol>
            {(ticket?.run_trace || []).slice(-30).map((entry, index) => (
              <li key={`${entry.timestamp}-${entry.agent}-${index}`}>
                <strong>{entry.agent}</strong>
                {entry.department_id ? ` · ${entry.department_id}` : ""}
                {entry.part ? ` · part ${entry.part}` : ""}
                <br />
                <small>{entry.timestamp}</small>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {ticket?.synthesis_brief ? (
        <section className="card-reveal">
          <h2>Brief Parte 1</h2>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
            {ticket.synthesis_brief}
          </pre>
        </section>
      ) : null}
    </div>
  );
}
