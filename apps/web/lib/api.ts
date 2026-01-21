const DEFAULT_API_BASE_URL = "http://localhost:8000";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export type TokenPair = {
  accessToken: string;
  refreshToken: string;
};

const ACCESS_TOKEN_KEY = "aion_access_token";
const REFRESH_TOKEN_KEY = "aion_refresh_token";

export function getTokens(): TokenPair | null {
  if (typeof window === "undefined") {
    return null;
  }
  const accessToken = window.localStorage.getItem(ACCESS_TOKEN_KEY);
  const refreshToken = window.localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!accessToken || !refreshToken) {
    return null;
  }
  return { accessToken, refreshToken };
}

export function setTokens(tokens: TokenPair) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
}

export function clearTokens() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function refreshTokens(): Promise<TokenPair | null> {
  const tokens = getTokens();
  if (!tokens) {
    return null;
  }
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: tokens.refreshToken })
  });
  if (!response.ok) {
    clearTokens();
    return null;
  }
  const data = (await response.json()) as {
    access_token: string;
    refresh_token: string;
  };
  const newTokens = {
    accessToken: data.access_token,
    refreshToken: data.refresh_token
  };
  setTokens(newTokens);
  return newTokens;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  authRequired = false
): Promise<T> {
  const headers = new Headers(options.headers ?? {});
  headers.set("Content-Type", "application/json");

  if (authRequired) {
    const tokens = getTokens();
    if (tokens) {
      headers.set("Authorization", `Bearer ${tokens.accessToken}`);
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  if (response.status === 401 && authRequired) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${refreshed.accessToken}`);
      const retry = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers
      });
      if (retry.ok) {
        return retry.json() as Promise<T>;
      }
    }
  }
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {})
    }
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Request failed");
  }

  return response.json() as Promise<T>;
}
