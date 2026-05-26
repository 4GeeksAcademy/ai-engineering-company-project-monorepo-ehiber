import { normalizeApiError } from "../errors/messages.js";

export const MANAGER_CONTEXT = {
  branches: [
    "central",
    "la_warehouse",
    "la_office",
    "zaragoza_warehouse",
    "zaragoza_office",
  ],
  branchLabels: {
    central: "Central",
    la_warehouse: "Los Angeles — Warehouse",
    la_office: "Los Angeles — Office",
    zaragoza_warehouse: "Zaragoza — Warehouse",
    zaragoza_office: "Zaragoza — Office",
  },
  categories: [
    "lost_parcel",
    "delivery_failure",
    "inventory_discrepancy",
    "carrier_issue",
    "returns_issue",
    "warehouse_incident",
    "system_failure",
    "client_complaint",
    "other",
  ],
  statuses: ["open", "in_progress", "resolved", "discarded"],
  origins: ["customer", "branch", "internal"],
  statusTransitions: {
    open: ["in_progress", "discarded"],
    in_progress: ["resolved", "discarded"],
  },
};

export function validateIncidentForm(values) {
  const errors = {};

  if (!values.title?.trim()) {
    errors.title = "Title is required.";
  } else if (values.title.trim().length < 3) {
    errors.title = "Title must be at least 3 characters.";
  }

  if (!values.description?.trim()) {
    errors.description = "Description is required.";
  } else if (values.description.trim().length < 5) {
    errors.description = "Description must be at least 5 characters.";
  }

  if (!MANAGER_CONTEXT.categories.includes(values.category)) {
    errors.category = "Choose a valid category.";
  }

  if (!MANAGER_CONTEXT.origins.includes(values.origin)) {
    errors.origin = "Choose a valid origin.";
  }

  if (!MANAGER_CONTEXT.branches.includes(values.branch)) {
    errors.branch = "Choose a valid branch.";
  }

  return errors;
}

export function getAllowedStatusTargets(currentStatus) {
  return MANAGER_CONTEXT.statusTransitions[currentStatus] || [];
}

export function parseApiFieldError(error) {
  return normalizeApiError(error);
}
