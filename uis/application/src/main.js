import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const CATEGORIES = [
  "carrier_last_mile",
  "carrier_international",
  "warehouse_supplies",
  "packaging_materials",
  "reverse_logistics",
  "fleet_maintenance",
  "it_and_wms_software",
  "cleaning_and_facilities",
];

const state = {
  suppliers: [],
  loadingList: false,
  savingById: {},
  error: "",
  formError: "",
  filters: { country: "", category: "" },
  form: {
    name: "",
    country: "USA",
    categories: ["carrier_last_mile"],
    rate_per_shipment: "",
    status: "active",
    service_zone: "",
    contact_email: "",
    notes: "",
  },
};

const app = document.querySelector("#app");

function render() {
  app.innerHTML = `
    <div class="shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">TrackFlow internal tools</p>
          <h1>Supplier Directory</h1>
        </div>
        <nav class="menu" aria-label="Application menu">
          <a class="menu-link active" href="#directory">Supplier Directory</a>
          <a class="menu-link" href="#register">Register Supplier</a>
        </nav>
      </header>

      <main class="layout">
        <section class="panel" id="directory">
          <div class="panel-head">
            <div>
              <p class="section-tag">Operations</p>
              <h2>Carrier and vendor registry</h2>
            </div>
            <button class="btn btn-secondary" id="refresh-btn" ${state.loadingList ? "disabled" : ""}>
              ${state.loadingList ? "Loading..." : "Refresh"}
            </button>
          </div>

          <div class="filters">
            <label>
              Country
              <select id="country-filter">
                <option value="">All countries</option>
                <option value="USA" ${state.filters.country === "USA" ? "selected" : ""}>USA</option>
                <option value="Spain" ${state.filters.country === "Spain" ? "selected" : ""}>Spain</option>
              </select>
            </label>
            <label>
              Category
              <select id="category-filter">
                <option value="">All categories</option>
                ${CATEGORIES.map(
                  (category) =>
                    `<option value="${category}" ${state.filters.category === category ? "selected" : ""}>${formatCategory(category)}</option>`
                ).join("")}
              </select>
            </label>
          </div>

          ${state.error ? `<p class="error-banner">${escapeHtml(state.error)}</p>` : ""}
          ${renderSupplierTable()}
        </section>

        <section class="panel" id="register">
          <p class="section-tag">Create</p>
          <h2>Register a new supplier</h2>
          <form class="form-grid" id="supplier-form">
            <label>Name<input name="name" required value="${escapeHtml(state.form.name)}" /></label>
            <label>
              Country
              <select name="country">
                <option value="USA" ${state.form.country === "USA" ? "selected" : ""}>USA</option>
                <option value="Spain" ${state.form.country === "Spain" ? "selected" : ""}>Spain</option>
              </select>
            </label>
            <label>
              Category
              <select name="category">
                ${CATEGORIES.map(
                  (category) =>
                    `<option value="${category}" ${state.form.categories[0] === category ? "selected" : ""}>${formatCategory(category)}</option>`
                ).join("")}
              </select>
            </label>
            <label>Rate per shipment<input name="rate_per_shipment" type="number" min="0.01" step="0.01" required value="${escapeHtml(state.form.rate_per_shipment)}" /></label>
            <label>Service zone<input name="service_zone" value="${escapeHtml(state.form.service_zone)}" /></label>
            <label>Contact email<input name="contact_email" type="email" value="${escapeHtml(state.form.contact_email)}" /></label>
            <label class="full-width">Notes<textarea name="notes">${escapeHtml(state.form.notes)}</textarea></label>
            <div class="full-width actions">
              <button class="btn btn-primary" type="submit">Create supplier</button>
            </div>
          </form>
          ${state.formError ? `<p class="error-banner">${escapeHtml(state.formError)}</p>` : ""}
        </section>
      </main>
    </div>
  `;

  bindEvents();
}

function renderSupplierTable() {
  if (state.loadingList) {
    return `<div class="empty-state"><p>Loading suppliers...</p></div>`;
  }

  if (!state.suppliers.length) {
    return `<div class="empty-state"><p>No suppliers found.</p><span>Try changing filters or register a new supplier.</span></div>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Country</th>
            <th>Categories</th>
            <th>Rate</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${state.suppliers
            .map(
              (supplier) => `
                <tr>
                  <td>
                    <strong>${escapeHtml(supplier.name)}</strong>
                    ${supplier.service_zone ? `<span class="muted">${escapeHtml(supplier.service_zone)}</span>` : ""}
                  </td>
                  <td>${escapeHtml(supplier.country)}</td>
                  <td>${supplier.categories.map(formatCategory).join(", ")}</td>
                  <td>
                    <div class="rate-cell">
                      <input type="number" min="0.01" step="0.01" value="${supplier.rate_per_shipment}" data-rate-input="${supplier.id}" ${state.savingById[supplier.id] ? "disabled" : ""} />
                      <span class="muted">${escapeHtml(supplier.currency)}</span>
                    </div>
                  </td>
                  <td><span class="badge badge-${supplier.status}">${supplier.status}</span></td>
                  <td class="row-actions">
                    <button class="btn btn-secondary" data-save-rate="${supplier.id}" ${state.savingById[supplier.id] ? "disabled" : ""}>Save rate</button>
                    <button class="btn btn-secondary" data-toggle-status="${supplier.id}" ${state.savingById[supplier.id] ? "disabled" : ""}>
                      ${supplier.status === "active" ? "Suspend" : "Activate"}
                    </button>
                  </td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function bindEvents() {
  document.querySelector("#refresh-btn")?.addEventListener("click", loadSuppliers);
  document.querySelector("#country-filter")?.addEventListener("change", (event) => {
    state.filters.country = event.target.value;
    loadSuppliers();
  });
  document.querySelector("#category-filter")?.addEventListener("change", (event) => {
    state.filters.category = event.target.value;
    loadSuppliers();
  });
  document.querySelector("#supplier-form")?.addEventListener("submit", handleCreateSupplier);

  document.querySelectorAll("[data-save-rate]").forEach((button) => {
    button.addEventListener("click", () => handleRateUpdate(Number(button.dataset.saveRate)));
  });

  document.querySelectorAll("[data-toggle-status]").forEach((button) => {
    button.addEventListener("click", () => handleStatusToggle(Number(button.dataset.toggleStatus)));
  });
}

async function loadSuppliers() {
  state.loadingList = true;
  state.error = "";
  render();

  const params = new URLSearchParams();
  if (state.filters.country) params.set("country", state.filters.country);
  if (state.filters.category) params.set("category", state.filters.category);

  try {
    const response = await fetch(`${API_BASE_URL}/suppliers?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(readError(payload));
    }
    state.suppliers = payload;
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loadingList = false;
    render();
  }
}

async function handleCreateSupplier(event) {
  event.preventDefault();
  state.formError = "";

  const formData = new FormData(event.target);
  const payload = {
    name: String(formData.get("name") || "").trim(),
    country: String(formData.get("country") || "USA"),
    categories: [String(formData.get("category") || "carrier_last_mile")],
    rate_per_shipment: Number(formData.get("rate_per_shipment")),
    status: "active",
    service_zone: String(formData.get("service_zone") || "").trim() || null,
    contact_email: String(formData.get("contact_email") || "").trim() || null,
    notes: String(formData.get("notes") || "").trim() || null,
  };

  try {
    const response = await fetch(`${API_BASE_URL}/suppliers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(readError(body));
    }

    event.target.reset();
    state.form = {
      name: "",
      country: "USA",
      categories: ["carrier_last_mile"],
      rate_per_shipment: "",
      status: "active",
      service_zone: "",
      contact_email: "",
      notes: "",
    };
    await loadSuppliers();
  } catch (error) {
    state.formError = error.message;
    render();
  }
}

async function handleRateUpdate(supplierId) {
  const input = document.querySelector(`[data-rate-input="${supplierId}"]`);
  const rate = Number(input?.value);
  if (!rate || rate <= 0) {
    state.error = "Rate must be greater than zero.";
    render();
    return;
  }

  state.savingById[supplierId] = true;
  state.error = "";
  render();

  try {
    const response = await fetch(`${API_BASE_URL}/suppliers/${supplierId}/rate`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rate_per_shipment: rate }),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(readError(body));
    }
    state.suppliers = state.suppliers.map((supplier) =>
      supplier.id === supplierId ? body : supplier
    );
  } catch (error) {
    state.error = error.message;
  } finally {
    delete state.savingById[supplierId];
    render();
  }
}

async function handleStatusToggle(supplierId) {
  const supplier = state.suppliers.find((item) => item.id === supplierId);
  if (!supplier) return;

  const nextStatus = supplier.status === "active" ? "suspended" : "active";
  state.savingById[supplierId] = true;
  state.error = "";
  render();

  try {
    const response = await fetch(`${API_BASE_URL}/suppliers/${supplierId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: nextStatus }),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(readError(body));
    }
    state.suppliers = state.suppliers.map((item) => (item.id === supplierId ? body : item));
  } catch (error) {
    state.error = error.message;
  } finally {
    delete state.savingById[supplierId];
    render();
  }
}

function readError(payload) {
  if (typeof payload?.detail === "string") return payload.detail;
  if (Array.isArray(payload?.detail)) {
    return payload.detail.map((item) => item.msg || JSON.stringify(item)).join(", ");
  }
  return "Request failed.";
}

function formatCategory(value) {
  return String(value).replaceAll("_", " ");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadSuppliers();
