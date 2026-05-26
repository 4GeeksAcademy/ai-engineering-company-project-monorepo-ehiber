import {
  MANAGER_CONTEXT,
  getAllowedStatusTargets,
  parseApiFieldError,
  validateIncidentForm,
} from "../../../packages/shared/incidents/constants.js";

export function createIncidentManager({ authClient, escapeHtml }) {
  const state = {
    incidents: [],
    summary: null,
    listLoading: false,
    listError: "",
    summaryLoading: false,
    summaryError: "",
    formValues: {
      title: "",
      description: "",
      category: MANAGER_CONTEXT.categories[0],
      origin: "customer",
      branch: "central",
    },
    formErrors: {},
    formMessage: "",
    formSubmitting: false,
    statusUpdating: {},
    filters: {
      status: "",
      origin: "",
      branch: "",
    },
  };

  async function loadIncidents() {
    state.listLoading = true;
    state.listError = "";
    render();

    const params = new URLSearchParams();
    if (state.filters.status) params.set("status", state.filters.status);
    if (state.filters.origin) params.set("origin", state.filters.origin);
    if (state.filters.branch) params.set("branch", state.filters.branch);

    try {
      const query = params.toString();
      state.incidents = await authClient.authFetch(`/api/incidents${query ? `?${query}` : ""}`);
    } catch (error) {
      state.listError = parseApiFieldError(error).message;
    } finally {
      state.listLoading = false;
      render();
    }
  }

  async function loadSummary() {
    state.summaryLoading = true;
    state.summaryError = "";
    render();

    try {
      state.summary = await authClient.authFetch("/api/incidents/summary");
    } catch (error) {
      state.summaryError = parseApiFieldError(error).message;
    } finally {
      state.summaryLoading = false;
      render();
    }
  }

  async function handleCreateSubmit(event) {
    event.preventDefault();
    const errors = validateIncidentForm(state.formValues);
    state.formErrors = errors;
    state.formMessage = "";

    if (Object.keys(errors).length) {
      render();
      return;
    }

    state.formSubmitting = true;
    render();

    try {
      await authClient.authFetch("/api/incidents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...state.formValues,
          status: "open",
        }),
      });
      state.formValues = {
        title: "",
        description: "",
        category: MANAGER_CONTEXT.categories[0],
        origin: "customer",
        branch: "central",
      };
      state.formMessage = "Incident registered successfully.";
      await Promise.all([loadIncidents(), loadSummary()]);
    } catch (error) {
      const parsed = parseApiFieldError(error);
      if (parsed.field) {
        state.formErrors = { ...state.formErrors, [parsed.field]: parsed.message };
      } else {
        state.formMessage = parsed.message;
      }
    } finally {
      state.formSubmitting = false;
      render();
    }
  }

  async function handleStatusChange(incidentId, currentStatus, nextStatus) {
    if (!nextStatus || nextStatus === currentStatus) return;

    const previous = state.incidents.map((item) => ({ ...item }));
    state.incidents = state.incidents.map((item) =>
      item.id === incidentId ? { ...item, status: nextStatus } : item,
    );
    state.statusUpdating[incidentId] = true;
    render();

    try {
      const updated = await authClient.authFetch(`/api/incidents/${incidentId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      state.incidents = state.incidents.map((item) => (item.id === incidentId ? updated : item));
      await loadSummary();
    } catch (error) {
      state.incidents = previous;
      state.listError = parseApiFieldError(error).message;
    } finally {
      delete state.statusUpdating[incidentId];
      render();
    }
  }

  function renderForm() {
    const branchHighlight =
      state.formValues.origin === "branch" ? " style='border: 2px solid var(--accent);'" : "";

    return `
      <section class="panel">
        <p class="section-tag">Register</p>
        <h2>Log a new incident</h2>
        <p class="lede">Capture operational issues in real time from any TrackFlow location.</p>
        <form id="incident-form" class="manager-form">
          <label>
            Title
            <input name="title" value="${escapeHtml(state.formValues.title)}" required />
            ${state.formErrors.title ? `<span class="field-error">${escapeHtml(state.formErrors.title)}</span>` : ""}
          </label>
          <label>
            Description
            <textarea name="description" rows="4" required>${escapeHtml(state.formValues.description)}</textarea>
            ${state.formErrors.description ? `<span class="field-error">${escapeHtml(state.formErrors.description)}</span>` : ""}
          </label>
          <label>
            Category
            <select name="category">
              ${MANAGER_CONTEXT.categories
                .map(
                  (value) =>
                    `<option value="${value}" ${state.formValues.category === value ? "selected" : ""}>${value}</option>`,
                )
                .join("")}
            </select>
            ${state.formErrors.category ? `<span class="field-error">${escapeHtml(state.formErrors.category)}</span>` : ""}
          </label>
          <label>
            Origin
            <select name="origin">
              ${MANAGER_CONTEXT.origins
                .map(
                  (value) =>
                    `<option value="${value}" ${state.formValues.origin === value ? "selected" : ""}>${value}</option>`,
                )
                .join("")}
            </select>
          </label>
          <label${branchHighlight}>
            Branch
            <select name="branch">
              ${MANAGER_CONTEXT.branches
                .map(
                  (value) =>
                    `<option value="${value}" ${state.formValues.branch === value ? "selected" : ""}>${MANAGER_CONTEXT.branchLabels[value]}</option>`,
                )
                .join("")}
            </select>
            ${state.formErrors.branch ? `<span class="field-error">${escapeHtml(state.formErrors.branch)}</span>` : ""}
          </label>
          ${
            state.formMessage
              ? `<p class="${state.formMessage.includes("success") ? "success-banner" : "error-banner"}">${escapeHtml(state.formMessage)}</p>`
              : ""
          }
          <button class="btn btn-primary" type="submit" ${state.formSubmitting ? "disabled" : ""}>
            ${state.formSubmitting ? "Saving..." : "Register incident"}
          </button>
        </form>
      </section>
    `;
  }

  function renderList() {
    return `
      <section class="panel">
        <p class="section-tag">Incidents</p>
        <h2>Active incident list</h2>
        <div class="filter-row">
          <select id="filter-status">
            <option value="">All statuses</option>
            ${MANAGER_CONTEXT.statuses.map((value) => `<option value="${value}" ${state.filters.status === value ? "selected" : ""}>${value}</option>`).join("")}
          </select>
          <select id="filter-origin">
            <option value="">All origins</option>
            ${MANAGER_CONTEXT.origins.map((value) => `<option value="${value}" ${state.filters.origin === value ? "selected" : ""}>${value}</option>`).join("")}
          </select>
          <select id="filter-branch">
            <option value="">All branches</option>
            ${MANAGER_CONTEXT.branches.map((value) => `<option value="${value}" ${state.filters.branch === value ? "selected" : ""}>${MANAGER_CONTEXT.branchLabels[value]}</option>`).join("")}
          </select>
          <button class="btn btn-secondary" id="retry-list-btn" type="button">Retry</button>
        </div>
        ${
          state.listLoading
            ? `<p class="muted">Loading incidents...</p>`
            : state.listError
              ? `<p class="error-banner">${escapeHtml(state.listError)} <button class="btn btn-secondary" id="retry-list-inline" type="button">Try again</button></p>`
              : !state.incidents.length
                ? `<div class="empty-state"><p>No incidents found.</p><span>Adjust filters or register a new incident.</span></div>`
                : `<div class="incident-table">${state.incidents
                    .map((incident) => {
                      const targets = getAllowedStatusTargets(incident.status);
                      return `
                        <article class="incident-card">
                          <div>
                            <strong>${escapeHtml(incident.title)}</strong>
                            <p class="muted">${escapeHtml(incident.category)} · ${escapeHtml(incident.origin)} · ${escapeHtml(MANAGER_CONTEXT.branchLabels[incident.branch] || incident.branch)}</p>
                          </div>
                          <label>
                            Status
                            <select data-incident-id="${incident.id}" data-current-status="${incident.status}" ${state.statusUpdating[incident.id] ? "disabled" : ""}>
                              <option value="${incident.status}">${incident.status}</option>
                              ${targets
                                .map((value) => `<option value="${value}">${value}</option>`)
                                .join("")}
                            </select>
                          </label>
                        </article>
                      `;
                    })
                    .join("")}</div>`
        }
      </section>
    `;
  }

  function renderSummaryPanel() {
    if (state.summaryLoading) {
      return `<section class="panel"><p class="muted">Loading summary...</p></section>`;
    }
    if (state.summaryError) {
      return `<section class="panel"><p class="error-banner">${escapeHtml(state.summaryError)} <button class="btn btn-secondary" id="retry-summary-btn" type="button">Try again</button></p></section>`;
    }
    if (!state.summary) {
      return `<section class="panel"><div class="empty-state"><p>No summary yet.</p></div></section>`;
    }

    return `
      <section class="panel">
        <p class="section-tag">Summary</p>
        <h2>Operational metrics</h2>
        <div class="metric-grid">
          <article class="metric-card"><span>Total incidents</span><strong>${state.summary.total}</strong></article>
        </div>
        <div class="results-columns">
          ${renderSummaryList("By status", state.summary.by_status)}
          ${renderSummaryList("By category", state.summary.by_category)}
          ${renderSummaryList("By origin", state.summary.by_origin)}
          ${renderSummaryList("By branch", state.summary.by_branch, true)}
        </div>
      </section>
    `;
  }

  function renderSummaryList(title, values, useBranchLabels = false) {
    const entries = Object.entries(values || {});
    return `
      <section class="list-panel">
        <h3>${title}</h3>
        ${
          entries.length
            ? `<dl>${entries
                .map(
                  ([key, value]) => `
                    <div class="list-row">
                      <dt>${escapeHtml(useBranchLabels ? MANAGER_CONTEXT.branchLabels[key] || key : key)}</dt>
                      <dd>${value}</dd>
                    </div>
                  `,
                )
                .join("")}</dl>`
            : `<p class="muted">No values available.</p>`
        }
      </section>
    `;
  }

  function render() {
    const root = document.querySelector("#incident-manager-root");
    if (!root) return;
    root.innerHTML = `
      <div class="manager-grid">
        ${renderForm()}
        ${renderList()}
        ${renderSummaryPanel()}
      </div>
    `;
    bindEvents();
  }

  function bindEvents() {
    document.querySelector("#incident-form")?.addEventListener("submit", handleCreateSubmit);
    document.querySelector("#incident-form")?.addEventListener("input", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement)) {
        return;
      }
      state.formValues[target.name] = target.value;
      if (state.formErrors[target.name]) {
        delete state.formErrors[target.name];
        render();
      }
    });

    document.querySelector("#filter-status")?.addEventListener("change", (event) => {
      state.filters.status = event.target.value;
      loadIncidents();
    });
    document.querySelector("#filter-origin")?.addEventListener("change", (event) => {
      state.filters.origin = event.target.value;
      loadIncidents();
    });
    document.querySelector("#filter-branch")?.addEventListener("change", (event) => {
      state.filters.branch = event.target.value;
      loadIncidents();
    });

    ["#retry-list-btn", "#retry-list-inline"].forEach((selector) => {
      document.querySelector(selector)?.addEventListener("click", loadIncidents);
    });
    document.querySelector("#retry-summary-btn")?.addEventListener("click", loadSummary);

    document.querySelectorAll("[data-incident-id]").forEach((select) => {
      select.addEventListener("change", (event) => {
        const incidentId = Number(event.target.dataset.incidentId);
        const currentStatus = event.target.dataset.currentStatus;
        handleStatusChange(incidentId, currentStatus, event.target.value);
      });
    });
  }

  return {
    mount() {
      loadIncidents();
      loadSummary();
    },
    render,
  };
}
