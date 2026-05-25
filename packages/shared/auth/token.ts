import { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from "./constants";
import type { UserPublic } from "./types";

export const getStoredToken = (): string | null => {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
};

export const setStoredToken = (token: string): void => {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
};

export const clearStoredSession = (): void => {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(USER_STORAGE_KEY);
};

export const getStoredUser = (): UserPublic | null => {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as UserPublic;
  } catch {
    return null;
  }
};

export const setStoredUser = (user: UserPublic): void => {
  window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
};

export const isAuthenticated = (): boolean => Boolean(getStoredToken());
