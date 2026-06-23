"use client";

import { FormEvent, useState } from "react";
import { incidentsApi } from "@/lib/incidents-api";
import { useIncidentsData } from "@/lib/hooks/use-incidents-data";
import type {
  IncidentBranch,
  IncidentCategory,
  IncidentCreate,
  IncidentOrigin,
  IncidentStatus,
} from "@/lib/incidents-types";
import {
  INCIDENT_BRANCHES,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUS_TRANSITIONS,
  INCIDENT_STATUSES,
} from "@/lib/incidents-types";

const initialForm: IncidentCreate = {
  title: "",
  description: "",
  category: "lost_parcel",
  status: "open",
  origin: "customer",
  branch: "central",
};

export default function IncidentsPage() {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState<IncidentCreate>(initialForm);

  const [statusFilter, setStatusFilter] = useState<"all" | IncidentStatus>("all");
  const [originFilter, setOriginFilter] = useState<"all" | IncidentOrigin>("all");
  const [branchFilter, setBranchFilter] = useState<"all" | IncidentBranch>("all");
  const [categoryFilter, setCategoryFilter] = useState<"all" | IncidentCategory>("all");
  const { incidents, setIncidents, summary, setSummary, loading, loadError, refresh, parseFieldError } =
    useIncidentsData({
      statusFilter,
      originFilter,
      branchFilter,
      categoryFilter,
    });

  const updateStatus = async (incidentId: number, status: IncidentStatus) => {
    setError("");
    try {
      const updated = await incidentsApi.updateStatus(incidentId, status);
      setIncidents((current) =>
        current.map((incident) => (incident.id === incidentId ? updated : incident)),
      );
      const latestSummary = await incidentsApi.summary();
      setSummary(latestSummary);
    } catch (statusError) {
      setError(statusError instanceof Error ? parseFieldError(statusError.message) : "No se pudo actualizar status.");
    }
  };

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      await incidentsApi.create(form);
      setForm(initialForm);
      setSuccess("Incidente creado correctamente.");
      await refresh();
    } catch (createError) {
      setError(createError instanceof Error ? parseFieldError(createError.message) : "No se pudo crear incidente.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main>
      <header className="page-head card-reveal">
        <p className="kicker">Consolidated Module</p>
        <h2>Incidents</h2>
        <p className="muted">
          Modulo conectado a API real para crear, listar y actualizar status de incidentes.
        </p>
      </header>

      <section className="panel card-reveal">
        <h3>Nuevo incidente</h3>
        <form className="form-grid two-col" onSubmit={handleCreate}>
          <label>
            Title
            <input
              className="input"
              value={form.title}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              required
            />
          </label>

          <label>
            Category
            <select
              className="input"
              value={form.category}
              onChange={(event) =>
                setForm((current) => ({ ...current, category: event.target.value as IncidentCategory }))
              }
            >
              {INCIDENT_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>

          <label>
            Origin
            <select
              className="input"
              value={form.origin}
              onChange={(event) =>
                setForm((current) => ({ ...current, origin: event.target.value as IncidentOrigin }))
              }
            >
              {INCIDENT_ORIGINS.map((origin) => (
                <option key={origin} value={origin}>
                  {origin}
                </option>
              ))}
            </select>
          </label>

          <label>
            Branch
            <select
              className="input"
              value={form.branch}
              onChange={(event) =>
                setForm((current) => ({ ...current, branch: event.target.value as IncidentBranch }))
              }
            >
              {INCIDENT_BRANCHES.map((branch) => (
                <option key={branch} value={branch}>
                  {branch}
                </option>
              ))}
            </select>
          </label>

          <label style={{ gridColumn: "1 / -1" }}>
            Description
            <textarea
              className="input"
              rows={4}
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              required
            />
          </label>

          <button className="button-primary" type="submit" disabled={saving}>
            {saving ? "Guardando..." : "Crear incidente"}
          </button>
        </form>

        {error ? <p className="notice notice-error">{error}</p> : null}
        {success ? <p className="notice notice-success">{success}</p> : null}
      </section>

      <section className="panel card-reveal">
        <h3>Operational Snapshot</h3>
        <div className="stats-grid">
          <article className="stat-card">
            <span>Total incidents</span>
            <strong>{summary?.total ?? 0}</strong>
          </article>
          <article className="stat-card">
            <span>Open</span>
            <strong>{summary?.by_status.open ?? 0}</strong>
          </article>
          <article className="stat-card">
            <span>In Progress</span>
            <strong>{summary?.by_status.in_progress ?? 0}</strong>
          </article>
          <article className="stat-card">
            <span>Resolved</span>
            <strong>{summary?.by_status.resolved ?? 0}</strong>
          </article>
        </div>

        <div className="filters-grid">
          <label>
            Status
            <select
              className="input"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as "all" | IncidentStatus)}
            >
              <option value="all">all</option>
              {INCIDENT_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>

          <label>
            Origin
            <select
              className="input"
              value={originFilter}
              onChange={(event) => setOriginFilter(event.target.value as "all" | IncidentOrigin)}
            >
              <option value="all">all</option>
              {INCIDENT_ORIGINS.map((origin) => (
                <option key={origin} value={origin}>
                  {origin}
                </option>
              ))}
            </select>
          </label>

          <label>
            Branch
            <select
              className="input"
              value={branchFilter}
              onChange={(event) => setBranchFilter(event.target.value as "all" | IncidentBranch)}
            >
              <option value="all">all</option>
              {INCIDENT_BRANCHES.map((branch) => (
                <option key={branch} value={branch}>
                  {branch}
                </option>
              ))}
            </select>
          </label>

          <label>
            Category
            <select
              className="input"
              value={categoryFilter}
              onChange={(event) => setCategoryFilter(event.target.value as "all" | IncidentCategory)}
            >
              <option value="all">all</option>
              {INCIDENT_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
        </div>

        {loading ? <p className="muted">Cargando incidentes...</p> : null}
        {!loading && (error || loadError) ? (
          <p className="notice notice-error">{error || loadError}</p>
        ) : null}

        {!loading ? (
          <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Category</th>
                <th>Origin</th>
                <th>Branch</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((incident) => (
                <tr key={incident.id}>
                  <td>{incident.title}</td>
                  <td>{incident.category}</td>
                  <td>{incident.origin}</td>
                  <td>{incident.branch}</td>
                  <td>
                    <select
                      className="input"
                      value={incident.status}
                      onChange={(event) => updateStatus(incident.id, event.target.value as IncidentStatus)}
                    >
                      <option value={incident.status}>{incident.status}</option>
                      {INCIDENT_STATUS_TRANSITIONS[incident.status].map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        ) : null}
      </section>
    </main>
  );
}
