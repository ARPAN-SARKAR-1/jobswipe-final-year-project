import { API_BASE_URL, ApiError, getToken } from "@/lib/api";

function protectedResumeUrl(path: string): string {
  if (!API_BASE_URL) throw new ApiError("NEXT_PUBLIC_API_BASE_URL is not configured", 500);
  const api = new URL(API_BASE_URL);
  if (path.startsWith("/api/files/resumes/")) return `${api.origin}${path}`;
  const filename = path.split("/").pop();
  if (!filename) throw new ApiError("Resume file is unavailable", 400);
  return `${api.origin}/api/files/resumes/${filename}`;
}

export async function openProtectedResume(path: string) {
  const token = getToken();
  if (!token) throw new ApiError("Please login to view this file", 401);
  const response = await fetch(protectedResumeUrl(path), {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new ApiError("Resume file is not available for this account", response.status);
  }
  const blob = await response.blob();
  const objectUrl = window.URL.createObjectURL(blob);
  window.open(objectUrl, "_blank", "noopener,noreferrer");
  window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 60_000);
}
