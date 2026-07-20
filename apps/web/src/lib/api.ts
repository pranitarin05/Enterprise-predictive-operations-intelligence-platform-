/**
 * Centralized API client configuration.
 *
 * Every component/page should import API_BASE_URL from here instead of
 * hardcoding "http://localhost:8000" -- this is the ONE place that
 * changes between local dev and a real deployment.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  return response;
}
