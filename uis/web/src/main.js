import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const state = {
  file: null,
  summary: null,
  loading: false,
  error: "",
};

const app = document.querySelector("#app");

function render() {
  app.innerHTML = `
    <div class="shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">TrackFlow internal tools</p>
          <h1>Incident Analyzer Control Panel</h1>
        </div>
        <nav class="menu" aria-label="Application menu">
          <a class="menu-link active" href="#analyzer">Incident Analyzer</a>
          <a class="menu-link" href="#api">API Flow</a>
        </nav>
      </header>

      <main class="grid">
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

          <dl class="api-meta" id="api">
            <div>
              <dt>Analyze endpoint</dt>
              <dd>POST ${API_BASE_URL}/api/incidents/analyze</dd>
            </div>
            <div>
              <dt>Export endpoint</dt>
              <dd>GET ${API_BASE_URL}/api/incidents/results/export</dd>
            </div>
          </dl>

          ${state.error ? `<p class="error-banner">${escapeHtml(state.error)}</p>` : ""}
        </section>

        <section class="panel panel-results">
          <p class="section-tag">Summary</p>
          <h2>Latest analysis</h2>
          ${renderResults()}
        </section>
      </main>
    </div>
  `;

  bindEvents();
}

function renderResults() {
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
        summary.satisfaction.average_score === null ? "N/A" : summary.satisfaction.average_score
      )}
    </div>

    <div class="results-columns">
      ${renderDefinitionList("Category breakdown", summary.category_breakdown)}
      ${renderDefinitionList("Status breakdown", summary.status_breakdown)}
      ${renderDefinitionList("Invalid records by reason", summary.invalid_breakdown)}
    </div>

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
                  `
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
                  `
                )
                .join("")}
            </dl>`
          : `<p class="muted">No values available.</p>`
      }
    </section>
  `;
}

function bindEvents() {
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
}

async function handleAnalyze() {
  if (!state.file || state.loading) return;

  state.loading = true;
  state.error = "";
  render();

  const formData = new FormData();
  formData.append("file", state.file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/incidents/analyze`, {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Unable to analyze the file.");
    }
    state.summary = payload;
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    render();
  }
}

async function handleExport() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/incidents/results/export`);
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.detail || "Unable to export results.");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "results.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    state.error = error.message;
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
