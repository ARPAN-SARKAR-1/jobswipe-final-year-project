"use client";

import type { AuthResponse, Role, User } from "@/types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("jobswipe_token");
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem("jobswipe_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function saveAuth(auth: AuthResponse) {
  window.localStorage.setItem("jobswipe_token", auth.access_token);
  window.localStorage.setItem("jobswipe_user", JSON.stringify(auth.user));
  window.dispatchEvent(new Event("jobswipe-auth"));
}

export function logout() {
  window.localStorage.removeItem("jobswipe_token");
  window.localStorage.removeItem("jobswipe_user");
  window.dispatchEvent(new Event("jobswipe-auth"));
}

export function roleHome(role: Role): string {
  if (role === "ADMIN" || role === "OWNER") return "/admin/dashboard";
  if (role === "RECRUITER") return "/recruiter/dashboard";
  return "/jobseeker/dashboard";
}

export function assetUrl(path?: string | null): string | undefined {
  if (!path) return undefined;
  if (path.startsWith("http")) return path;
  if (!API_BASE_URL) return path;
  const api = new URL(API_BASE_URL);
  return `${api.origin}${path}`;
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!API_BASE_URL) {
    throw new ApiError("NEXT_PUBLIC_API_BASE_URL is not configured", 500);
  }

  const headers = new Headers(options.headers);
  const token = getToken();
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store"
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof data === "object" && data !== null && "detail" in data ? data.detail : data;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || item.message || "Validation error").join(", ")
      : String(detail || "Request failed");
    throw new ApiError(message, response.status);
  }

  return data as T;
}
