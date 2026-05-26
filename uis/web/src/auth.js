const TOKEN_STORAGE_KEY = "trackflow_access_token";
const USER_STORAGE_KEY = "trackflow_user";

export const getStoredToken = () => window.localStorage.getItem(TOKEN_STORAGE_KEY);

export const clearStoredSession = () => {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(USER_STORAGE_KEY);
};

export const setStoredSession = (token, user) => {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
};

export const isAuthenticated = () => Boolean(getStoredToken());

const parseError = async (response) => {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") return payload.detail;
    if (payload.detail && typeof payload.detail === "object" && !Array.isArray(payload.detail)) {
      return JSON.stringify(payload.detail);
    }
  } catch {
    return `Request failed with status ${response.status}.`;
  }
  return `Request failed with status ${response.status}.`;
};

export const createAuthClient = (apiBaseUrl) => {
  const baseUrl = apiBaseUrl.replace(/\/$/, "");

  const authFetch = async (path, init = {}, options = { auth: true }) => {
    const headers = new Headers(init.headers ?? {});

    if (options.auth !== false) {
      const token = getStoredToken();
      if (!token) {
        clearStoredSession();
        window.location.reload();
        throw new Error("Session expired.");
      }
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${baseUrl}${path}`, { ...init, headers });

    if (response.status === 401 && options.auth !== false) {
      clearStoredSession();
      window.location.reload();
      throw new Error("Session expired.");
    }

    if (!response.ok) {
      throw new Error(await parseError(response));
    }

    if (response.status === 204) return undefined;
    return response.json();
  };

  const login = async (email, password) => {
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

    const tokenPayload = await response.json();
    window.localStorage.setItem(TOKEN_STORAGE_KEY, tokenPayload.access_token);
    const user = await authFetch("/auth/me");
    setStoredSession(tokenPayload.access_token, user);
    return user;
  };

  const logout = () => {
    clearStoredSession();
    window.location.reload();
  };

  return { authFetch, login, logout };
};
