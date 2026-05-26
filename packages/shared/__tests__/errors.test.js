import { describe, expect, test } from "@jest/globals";
import { normalizeApiError, toUserMessage } from "../errors/messages.js";

describe("normalizeApiError", () => {
  test("returns field-aware API validation errors", () => {
    const error = new Error(JSON.stringify({ field: "branch", message: "Branch is not allowed." }));
    expect(normalizeApiError(error)).toEqual({
      field: "branch",
      message: "Branch is not allowed.",
    });
  });

  test("maps technical JSON errors to a friendly fallback", () => {
    const error = new Error("Unexpected token < in JSON at position 0");
    expect(toUserMessage(error, "We could not complete this request.")).toBe(
      "We could not complete this request.",
    );
  });
});
