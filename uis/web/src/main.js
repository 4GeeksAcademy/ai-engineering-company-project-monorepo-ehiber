import "./styles.css";
import { createAuthClient, isAuthenticated } from "./auth.js";
import { createIncidentManager } from "./incident-manager.js";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const authClient = createAuthClient(API_BASE_URL);
const incidentManager = createIncidentManager({ authClient, escapeHtml });

const state = {
  activeView: "analyzer",
  file: null,
  summary: null,
  loading: false,
  error: "",
  authLoading: false,
  authError: "",
};

const app = document.querySelector("#app");

function renderLogin() {
  app.innerHTML = `
    <div class="shell">
      <main class="panel" style="max-width: 520px; margin: 4rem auto;">
        <p class="section-tag">Secure access</p>
        <h2>Iniciar sesion</h2>
        <p class="lede">Accede al panel de incidencias de TrackFlow.</p>
        <form id="login-form" style="display: grid; gap: 1rem; margin-top: 1.5rem;">
          <label style="display: grid; gap: 0.5rem;">
            Email
            <input id="login-email" type="email" required />
          </label>
          <label style="display: grid; gap: 0.5rem;">
            Contrasena
            <input id="login-password" type="password" required />
          </label>
          ${state.authError ? `<p class="error-banner">${escapeHtml(state.authError)}</p>` : ""}
          <button class="btn btn-primary" type="submit" ${state.authLoading ? "disabled" : ""}>
            ${state.authLoading ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </main>
    </div>
  `;

  document.querySelector("#login-form")?.addEventListener("submit", handleLogin);
}

async function handleLogin(event) {
  event.preventDefault();
  state.authLoading = true;
  state.authError = "";
  renderLogin();

  try {
    await authClient.login(
      document.querySelector("#login-email").value,
      document.querySelector("#login-password").value,
    );
    render();
  } catch (error) {
    state.authError = error.message;
  } finally {
    state.authLoading = false;
    renderLogin();
  }
}

function render() {
  if (!isAuthenticated()) {
    renderLogin();
    return;
  }

  app.innerHTML = `
    <div class="shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">TrackFlow internal tools</p>
          <h1>${state.activeView === "manager" ? "Incident Manager" : "Incident Analyzer"}</h1>
        </div>
        <nav class="menu" aria-label="Application menu">
          <button class="menu-link ${state.activeView === "analyzer" ? "active" : ""}" id="nav-analyzer" type="button">Incident Analyzer</button>
          <button class="menu-link ${state.activeView === "manager" ? "active" : ""}" id="nav-manager" type="button">Incident Manager</button>
          <button class="menu-link" id="logout-btn" type="button">Cerrar sesion</button>
        </nav>
      </header>

      <main class="${state.activeView === "manager" ? "manager-shell" : "grid"}">
        ${state.activeView === "manager" ? `<div id="incident-manager-root"></div>` : renderAnalyzerView()}
      </main>
    </div>
  `;

  document.querySelector("#logout-btn")?.addEventListener("click", () => authClient.logout());
  document.querySelector("#nav-analyzer")?.addEventListener("click", () => {
    state.activeView = "analyzer";
    render();
  });
  document.querySelector("#nav-manager")?.addEventListener("click", () => {
    state.activeView = "manager";
    render();
    incidentManager.mount();
  });

  if (state.activeView === "analyzer") {
    bindAnalyzerEvents();
  } else {
    incidentManager.render();
  }
}

function renderAnalyzerView() {
  return `
    <section class="panel panel-upload" id="analyzer">
      <p class="section-tag">Upload</p>
      <h2>Validate and summarize logistics incidents</h2>
      <p class="lede">
        Upload the incident CSV, run the shared backend analysis, inspect invalid records, and export the latest summary.
      </p>

      <label class="dropzone ${state.file ? "dropzone-ready" : ""}" for="incident-file">
        <input id="incident-file" type="file" accept=".csv,text/csv" />
        <span class="drop-title">${state.file ? state.file.name : "Choose a CSV file"}</span>
        <span class="drop-subtitle">Drag and drop is optional. File selection works too.</span>
      </label>

      <div class="actions">
        <button class="btn btn-primary" id="analyze-btn" ${state.loading || !state.file ? "disabled" : ""}>
          ${state.loading ? "Analyzing..." : "Analyze file"}
        </button>
        <button class="btn btn-secondary" id="export-btn" ${state.summary ? "" : "disabled"}>
          Download results CSV
        </button>
      </div>

      ${state.error ? `<p class="error-banner">${escapeHtml(state.error)} <button class="btn btn-secondary" id="retry-analyze-btn" type="button">Try again</button></p>` : ""}
    </section>

    <section class="panel panel-results">
      <p class="section-tag">Summary</p>
      <h2>Latest analysis</h2>
      ${renderResults()}
    </section>
  `;
}

function renderResults() {
  if (state.loading) {
    return `<p class="muted">Analyzing file...</p>`;
  }

  if (!state.summary) {
    return `
      <div class="empty-state">
        <p>No analysis loaded yet.</p>
        <span>Run the analyzer to see totals, breakdowns, invalid rows, and satisfaction metrics.</span>
      </div>
    `;
  }

  const summary = state.summary;
  return `
    <div class="metric-grid">
      ${renderMetricCard("Total records", summary.totals.total_records)}
      ${renderMetricCard("Valid records", summary.totals.valid_records)}
      ${renderMetricCard("Invalid records", summary.totals.invalid_records)}
      ${renderMetricCard(
        "Average satisfaction",
        summary.satisfaction.average_score === null ? "N/A" : summary.satisfaction.average_score,
      )}
    </div>

    <div class="results-columns">
      ${renderDefinitionList("Category breakdown", summary.category_breakdown)}
      ${renderDefinitionList("Status breakdown", summary.status_breakdown)}
      ${renderDefinitionList("Country breakdown", summary.country_breakdown)}
      ${renderDefinitionList("Invalid records by reason", summary.invalid_breakdown)}
    </div>

    ${renderScoreDistribution(summary.satisfaction)}

    <section class="invalid-section">
      <h3>Invalid record details</h3>
      ${
        summary.invalid_details.length
          ? `<ul class="invalid-list">
              ${summary.invalid_details
                .map(
                  (item) => `
                    <li>
                      <strong>Row ${item.row_number}</strong>
                      <span>${escapeHtml(item.reasons.join(", "))}</span>
                    </li>
                  `,
                )
                .join("")}
            </ul>`
          : `<p class="muted">No invalid records detected.</p>`
      }
    </section>
  `;
}

function renderMetricCard(label, value) {
  return `
    <article class="metric-card">
      <span>${label}</span>
      <strong>${value}</strong>
    </article>
  `;
}

function renderDefinitionList(title, values) {
  const entries = Object.entries(values || {});
  return `
    <section class="list-panel">
      <h3>${title}</h3>
      ${
        entries.length
          ? `<dl>
              ${entries
                .map(
                  ([key, value]) => `
                    <div class="list-row">
                      <dt>${escapeHtml(key)}</dt>
                      <dd>${value}</dd>
                    </div>
                  `,
                )
                .join("")}
            </dl>`
          : `<p class="muted">No values available.</p>`
      }
    </section>
  `;
}

function renderScoreDistribution(satisfaction) {
  const distribution = satisfaction?.score_distribution || {};
  const entries = Object.entries(distribution);
  if (!entries.length) {
    return "";
  }

  return `
    <section class="list-panel">
      <h3>Satisfaction score distribution</h3>
      <dl>
        ${entries
          .map(
            ([score, count]) => `
              <div class="list-row">
                <dt>Score ${escapeHtml(score)}</dt>
                <dd>${count}</dd>
              </div>
            `,
          )
          .join("")}
      </dl>
    </section>
  `;
}

function bindAnalyzerEvents() {
  const input = document.querySelector("#incident-file");
  const analyzeButton = document.querySelector("#analyze-btn");
  const exportButton = document.querySelector("#export-btn");
  const dropzone = document.querySelector(".dropzone");

  input?.addEventListener("change", (event) => {
    state.file = event.target.files?.[0] || null;
    state.error = "";
    render();
  });

  dropzone?.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("dropzone-hover");
  });

  dropzone?.addEventListener("dragleave", () => {
    dropzone.classList.remove("dropzone-hover");
  });

  dropzone?.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("dropzone-hover");
    const file = event.dataTransfer?.files?.[0] || null;
    if (file) {
      state.file = file;
      state.error = "";
      render();
    }
  });

  analyzeButton?.addEventListener("click", handleAnalyze);
  exportButton?.addEventListener("click", handleExport);
  document.querySelector("#retry-analyze-btn")?.addEventListener("click", handleAnalyze);
}

async function handleAnalyze() {
  if (!state.file || state.loading) return;

  state.loading = true;
  state.error = "";
  render();

  const formData = new FormData();
  formData.append("file", state.file);

  try {
    state.summary = await authClient.authFetch("/api/incidents/analyze", {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    state.error = "We could not analyze this file. Check the CSV format and try again.";
  } finally {
    state.loading = false;
    render();
  }
}

async function handleExport() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/incidents/results/export`, {
      headers: { Authorization: `Bearer ${window.localStorage.getItem("trackflow_access_token")}` },
    });
    if (response.status === 401) {
      authClient.logout();
      return;
    }
    if (!response.ok) {
      throw new Error("Unable to export results.");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "results.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  } catch {
    state.error = "We could not download the results file. Please try again.";
    render();
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

render();
