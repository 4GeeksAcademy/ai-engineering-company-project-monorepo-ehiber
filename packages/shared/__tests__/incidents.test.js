import { describe, expect, test } from "@jest/globals";
import { getAllowedStatusTargets, parseApiFieldError, validateIncidentForm } from "../incidents/constants.js";

describe("validateIncidentForm", () => {
  test("accepts a valid incident payload", () => {
    const errors = validateIncidentForm({
      title: "Carrier delay in Zaragoza",
      description: "Shipment stuck at sorting facility overnight.",
      category: "carrier_issue",
      origin: "branch",
      branch: "zaragoza_warehouse",
    });

    expect(errors).toEqual({});
  });

  test("flags missing description", () => {
    const errors = validateIncidentForm({
      title: "Missing description",
      description: "",
      category: "carrier_issue",
      origin: "branch",
      branch: "zaragoza_warehouse",
    });

    expect(errors.description).toBe("Description is required.");
  });
});

describe("getAllowedStatusTargets", () => {
  test("returns valid transitions for open incidents", () => {
    expect(getAllowedStatusTargets("open")).toEqual(["in_progress", "discarded"]);
  });

  test("returns no transitions for final states", () => {
    expect(getAllowedStatusTargets("resolved")).toEqual([]);
  });
});

describe("parseApiFieldError", () => {
  test("delegates structured API errors to the shared normalizer", () => {
    const error = new Error(JSON.stringify({ field: "category", message: "Category is not allowed." }));
    expect(parseApiFieldError(error)).toEqual({
      field: "category",
      message: "Category is not allowed.",
    });
  });
});
