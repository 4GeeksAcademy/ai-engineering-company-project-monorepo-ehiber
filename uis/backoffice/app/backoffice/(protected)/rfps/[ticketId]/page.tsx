"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  approveRfpIntake,
  getRfpTicket,
  type RfpTicketDetail,
} from "@/lib/rfp-api";

const ACTIVE_STATUSES = new Set([
  "analizando",
  "generando_borrador",
  "en_evaluación",
]);

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
            {busy ? "Confirmando…" : "Confirmar intake y continuar"}
          </button>
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
        <h2>Legibilidad / coste estimado</h2>
        <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem" }}>
          {JSON.stringify(
            {
              readability: ticket?.readability_metrics,
              cost: ticket?.processing_cost_estimate,
            },
            null,
            2,
          )}
        </pre>
      </section>

      <section className="card-reveal">
        <h2>Por departamento</h2>
        {(ticket?.sections || []).length === 0 ? (
          <p>Sin secciones (documento descartado o aún analizando).</p>
        ) : (
          (ticket?.sections || []).map((section) => (
            <article key={section.department_id} style={{ marginBottom: "1.25rem" }}>
              <h3>
                {section.department_id} · {section.approver}
              </h3>
              <ul>
                {section.key_aspects.map((aspect) => (
                  <li key={aspect}>{aspect}</li>
                ))}
              </ul>
            </article>
          ))
        )}
      </section>

      {ticket?.synthesis_brief ? (
        <section className="card-reveal">
          <h2>Brief para Sales</h2>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
            {ticket.synthesis_brief}
          </pre>
        </section>
      ) : null}
    </div>
  );
}
