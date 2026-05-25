import { createAuthClient } from "@repo/shared/auth";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_TRACKFLOW_API_URL ?? "http://localhost:8000";

export const authClient = createAuthClient(apiBaseUrl);
