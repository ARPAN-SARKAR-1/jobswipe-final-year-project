const DRAFT_PREFIX = "sfs_jobseeker_profile_draft_";

export type JobSeekerProfileDraft<T> = {
  form: T;
  username: string;
  visibility: "PUBLIC" | "PRIVATE";
  savedAt: string;
};

export function profileDraftKey(userKey?: string | number | null) {
  return `${DRAFT_PREFIX}${userKey || "current"}`;
}

export function loadProfileDraft<T>(userKey?: string | number | null): JobSeekerProfileDraft<T> | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(profileDraftKey(userKey));
  if (!raw) return null;
  try {
    return JSON.parse(raw) as JobSeekerProfileDraft<T>;
  } catch {
    window.localStorage.removeItem(profileDraftKey(userKey));
    return null;
  }
}

export function saveProfileDraft<T>(userKey: string | number | null | undefined, draft: JobSeekerProfileDraft<T>) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(profileDraftKey(userKey), JSON.stringify(draft));
}

export function clearProfileDraft(userKey?: string | number | null) {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(profileDraftKey(userKey));
}
