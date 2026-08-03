"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  listRfpTickets,
  uploadRfpPdf,
  type RfpTicketSummary,
} from "@/lib/rfp-api";

const ACTIVE_STATUSES = new Set([
  "analizando",
  "generando_borrador",
  "en_evaluación",
]);

export default function RfpTicketsPage() {
  const router = useRouter();
  const [tickets, setTickets] = useState<RfpTicketSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await listRfpTickets();
      setTickets(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudieron cargar los tickets.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const hasActive = tickets.some((t) => ACTIVE_STATUSES.has(t.status));
    if (!hasActive) return;
    const id = window.setInterval(() => {
      void refresh();
    }, 2500);
    return () => window.clearInterval(id);
  }, [tickets, refresh]);

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setError("Selecciona un PDF de RFP.");
      return;
    }
    setUploading(true);
    setError("");
    try {
      const created = await uploadRfpPdf(file);
      setFile(null);
      router.push(`/backoffice/rfps/${created.ticket_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al subir el PDF.");
      setUploading(false);
    }
  };

  return (
    <div className="page-stack">
      <header className="page-header">
        <p className="kicker">Sales · Miguel Torres</p>
        <h1>RFP Intake</h1>
        <p>
          Sube RFPs en PDF, clasifica si son válidas y reparte el análisis por
          departamento (Warehouse, Last Mile, Reverse).
        </p>
      </header>

      <form className="card-reveal form-grid" onSubmit={handleUpload}>
        <label htmlFor="rfp-file">PDF de RFP</label>
        <input
          id="rfp-file"
          type="file"
          accept="application/pdf,.pdf"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <button type="submit" disabled={uploading || !file}>
          {uploading ? "Subiendo…" : "Crear ticket"}
        </button>
      </form>

      {error ? <p className="form-error">{error}</p> : null}

      <section className="card-reveal">
        <h2>Tickets</h2>
        {loading ? <p>Cargando…</p> : null}
        {!loading && tickets.length === 0 ? (
          <p>No hay tickets todavía. Sube el primer PDF.</p>
        ) : null}
        <ul className="side-nav" style={{ listStyle: "none", padding: 0 }}>
          {tickets.map((ticket) => (
            <li key={ticket.ticket_id} style={{ marginBottom: "0.75rem" }}>
              <Link
                href={`/backoffice/rfps/${ticket.ticket_id}`}
                className="nav-link"
              >
                <strong>{ticket.client_name || ticket.original_filename}</strong>
                {" · "}
                <span>{ticket.status}</span>
                {ticket.departments_needed?.length ? (
                  <>
                    {" · "}
                    {ticket.departments_needed.join(", ")}
                  </>
                ) : null}
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
