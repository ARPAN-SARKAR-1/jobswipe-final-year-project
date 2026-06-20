"use client";

import type { AuthResponse, PaginatedResponse, Role, SupportTicket, SupportTicketCreate, SupportTicketStatus, User } from "@/types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/+$/, "") ?? "";

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
  if (!auth.access_token || !auth.user) {
    throw new ApiError("Authentication is not complete", 401);
  }
  window.localStorage.setItem("jobswipe_token", auth.access_token);
  window.localStorage.setItem("jobswipe_user", JSON.stringify(auth.user));
  window.dispatchEvent(new Event("jobswipe-auth"));
}

export function logout() {
  window.localStorage.removeItem("jobswipe_token");
  window.localStorage.removeItem("jobswipe_user");
  window.dispatchEvent(new Event("jobswipe-auth"));
}

export function roleHome(role: Role, selectedPortal?: Role | null): string {
  if (role === "OWNER" && (selectedPortal === "OWNER" || selectedPortal === "ADMIN")) return "/admin/dashboard";
  if (role === "ADMIN" || role === "OWNER") return "/admin/dashboard";
  if (role === "RECRUITER") return "/recruiter/dashboard";
  return "/jobseeker/dashboard";
}

export function getPostAuthRedirect(role: Role): string {
  if (role === "RECRUITER") return "/recruiter/settings/profile";
  if (role === "JOB_SEEKER") return "/jobseeker/settings/profile";
  return "/admin/dashboard";
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
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  const headers = new Headers(options.headers);
  const token = getToken();
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  const startedAt = Date.now();
  let slowRequest = false;
  const slowTimer = window.setTimeout(() => {
    slowRequest = true;
    console.info("API request is still pending", { path: normalizedPath });
  }, 15000);
  try {
    response = await fetch(`${API_BASE_URL}${normalizedPath}`, {
      ...options,
      headers,
      cache: "no-store"
    });
  } catch (error) {
    const elapsedMs = Date.now() - startedAt;
    console.error("API request failed", {
      path: normalizedPath,
      elapsedMs,
      message: error instanceof Error ? error.message : "Unknown network error"
    });
    throw new ApiError(
      slowRequest || elapsedMs >= 15000
        ? "The server is taking longer than expected. Please refresh in a few seconds."
        : "Request could not reach the server. Please check your connection and try again.",
      0
    );
  } finally {
    window.clearTimeout(slowTimer);
  }

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

export function createSupportTicket(payload: SupportTicketCreate) {
  return apiFetch<SupportTicket>("/support/tickets", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getMySupportTickets() {
  return apiFetch<SupportTicket[]>("/support/my-tickets");
}

export function getAdminSupportTickets(query: string) {
  return apiFetch<PaginatedResponse<SupportTicket>>(`/admin/support-tickets${query ? `?${query}` : ""}`);
}

export function updateSupportTicket(id: number, payload: Partial<Pick<SupportTicket, "priority" | "status" | "assigned_admin_id" | "admin_note">>) {
  return apiFetch<SupportTicket>(`/admin/support-tickets/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function resolveSupportTicket(id: number, adminNote?: string) {
  return apiFetch<SupportTicket>(`/admin/support-tickets/${id}/resolve`, {
    method: "POST",
    body: JSON.stringify({ admin_note: adminNote || null })
  });
}

export function closeSupportTicket(id: number, adminNote?: string) {
  return apiFetch<SupportTicket>(`/admin/support-tickets/${id}/close`, {
    method: "POST",
    body: JSON.stringify({ admin_note: adminNote || null })
  });
}

export function supportTicketStatusLabel(status: SupportTicketStatus) {
  return status.replaceAll("_", " ");
}
