const dangerousExtensions = new Set([".exe", ".bat", ".cmd", ".js", ".html", ".php", ".py", ".sh", ".jar", ".zip", ".pem", ".key", ".crt"]);

export const uploadRules = {
  resume: {
    maxBytes: 5 * 1024 * 1024,
    allowedMimeTypes: new Set(["application/pdf"]),
    allowedExtensions: new Set([".pdf"])
  },
  image: {
    maxBytes: 2 * 1024 * 1024,
    allowedMimeTypes: new Set(["image/jpeg", "image/png", "image/webp"]),
    allowedExtensions: new Set([".jpg", ".jpeg", ".png", ".webp"])
  }
};

export function validateUploadFile(file: File, rules: (typeof uploadRules)[keyof typeof uploadRules]): string | null {
  if (file.size > rules.maxBytes) return "File size exceeds allowed limit.";
  const extension = file.name.includes(".") ? `.${file.name.split(".").pop()?.toLowerCase() || ""}` : "";
  if (dangerousExtensions.has(extension)) return "Invalid file type.";
  if (!rules.allowedExtensions.has(extension)) return "Invalid file type.";
  if (!rules.allowedMimeTypes.has(file.type)) return "Invalid file type.";
  return null;
}
