const DEFAULT_MESSAGE = "Something went wrong. Please try again.";

export function normalizeApiError(error, fallback = DEFAULT_MESSAGE) {
  if (!error) {
    return { message: fallback, field: null };
  }

  const rawMessage = error instanceof Error ? error.message : String(error);

  try {
    const payload = JSON.parse(rawMessage);
    if (payload?.field && payload?.message) {
      return { field: payload.field, message: payload.message };
    }
  } catch {
    // Fall through to plain text handling.
  }

  if (/unexpected token|json|status 5\d\d|internal server error/i.test(rawMessage)) {
    return { message: fallback, field: null };
  }

  return { message: rawMessage || fallback, field: null };
}

export function toUserMessage(error, fallback = DEFAULT_MESSAGE) {
  return normalizeApiError(error, fallback).message;
}
