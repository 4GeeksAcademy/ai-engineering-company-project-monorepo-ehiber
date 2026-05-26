import {
  clearStoredSession,
  getStoredToken,
  setStoredToken,
  setStoredUser,
} from "./token";
import type { ApiErrorPayload, TokenResponse, UserPublic } from "./types";

const parseError = async (response: Response): Promise<string> => {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (payload.detail && typeof payload.detail === "object" && !Array.isArray(payload.detail)) {
      return JSON.stringify(payload.detail);
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail.map((item) => item.msg ?? "Validation error").join(". ");
    }
  } catch {
    if (response.status >= 500) {
      return "The service is temporarily unavailable. Please try again.";
    }
    return `Request failed with status ${response.status}.`;
  }

  if (response.status >= 500) {
    return "The service is temporarily unavailable. Please try again.";
  }

  return `Request failed with status ${response.status}.`;
};

const handleUnauthorized = (): never => {
  clearStoredSession();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
  throw new Error("Session expired.");
};

export const createAuthClient = (apiBaseUrl: string) => {
  const baseUrl = apiBaseUrl.replace(/\/$/, "");

  const authFetch = async <T>(
    path: string,
    init: RequestInit = {},
    options: { auth?: boolean } = { auth: true },
  ): Promise<T> => {
    const headers = new Headers(init.headers ?? {});

    if (options.auth !== false) {
      const token = getStoredToken();
      if (!token) {
        handleUnauthorized();
      }
      headers.set("Authorization", `Bearer ${token}`);
    }

    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
    });

    if (response.status === 401 && options.auth !== false) {
      handleUnauthorized();
    }

    if (!response.ok) {
      throw new Error(await parseError(response));
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  };

  const login = async (email: string, password: string): Promise<UserPublic> => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);

    const response = await fetch(`${baseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });

    if (!response.ok) {
      throw new Error(await parseError(response));
    }

    const tokenPayload = (await response.json()) as TokenResponse;
    setStoredToken(tokenPayload.access_token);

    const user = await authFetch<UserPublic>("/auth/me");
    setStoredUser(user);
    return user;
  };

  const register = async (email: string, password: string): Promise<UserPublic> => {
    const response = await fetch(`${baseUrl}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error(await parseError(response));
    }

    const tokenPayload = (await response.json()) as TokenResponse;
    setStoredToken(tokenPayload.access_token);

    const user = await authFetch<UserPublic>("/auth/me");
    setStoredUser(user);
    return user;
  };

  const logout = (): void => {
    clearStoredSession();
    window.location.href = "/login";
  };

  const updateProfile = async (userId: number, email: string): Promise<UserPublic> => {
    const user = await authFetch<UserPublic>(`/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify({ email }),
    });
    setStoredUser(user);
    return user;
  };

  const changePassword = async (
    currentPassword: string,
    newPassword: string,
  ): Promise<void> => {
    await authFetch<void>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  };

  const requestPasswordReset = async (email: string): Promise<string> => {
    const response = await fetch(`${baseUrl}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      throw new Error(await parseError(response));
    }

    const payload = (await response.json()) as { message: string };
    return payload.message;
  };

  const resetPassword = async (token: string, newPassword: string): Promise<void> => {
    const response = await fetch(`${baseUrl}/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password: newPassword }),
    });

    if (!response.ok) {
      throw new Error(await parseError(response));
    }
  };

  return {
    authFetch,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    requestPasswordReset,
    resetPassword,
    getCurrentUser: async (): Promise<UserPublic> => authFetch<UserPublic>("/auth/me"),
  };
};

export type AuthClient = ReturnType<typeof createAuthClient>;
