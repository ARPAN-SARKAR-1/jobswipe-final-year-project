export const MB = 1024 * 1024;

export type FileValidationRule = {
  label: string;
  maxMb: number;
  extensions: string[];
  mimeTypes: string[];
  accept: string;
  typeMessage: string;
};

export const uploadRules = {
  profilePhoto: {
    label: "Profile photo",
    maxMb: 2,
    extensions: [".jpg", ".jpeg", ".png", ".webp"],
    mimeTypes: ["image/jpeg", "image/png", "image/webp"],
    accept: "image/png,image/jpeg,image/webp",
    typeMessage: "Only JPG, PNG, or WEBP files are allowed."
  },
  companyLogo: {
    label: "Company logo",
    maxMb: 2,
    extensions: [".jpg", ".jpeg", ".png", ".webp"],
    mimeTypes: ["image/jpeg", "image/png", "image/webp"],
    accept: "image/png,image/jpeg,image/webp",
    typeMessage: "Only JPG, PNG, or WEBP files are allowed."
  },
  resume: {
    label: "Resume",
    maxMb: 5,
    extensions: [".pdf", ".doc", ".docx"],
    mimeTypes: ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    accept: "application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.doc,.docx",
    typeMessage: "Only PDF, DOC, or DOCX files are allowed."
  },
  studentProof: {
    label: "Student proof",
    maxMb: 3,
    extensions: [".pdf", ".jpg", ".jpeg", ".png", ".webp"],
    mimeTypes: ["application/pdf", "image/jpeg", "image/png", "image/webp"],
    accept: "application/pdf,image/png,image/jpeg,image/webp",
    typeMessage: "Only PDF, JPG, PNG, or WEBP files are allowed."
  },
  verificationDocument: {
    label: "Verification document",
    maxMb: 5,
    extensions: [".pdf", ".jpg", ".jpeg", ".png", ".webp"],
    mimeTypes: ["application/pdf", "image/jpeg", "image/png", "image/webp"],
    accept: "application/pdf,image/png,image/jpeg,image/webp",
    typeMessage: "Only PDF, JPG, PNG, or WEBP files are allowed."
  }
} satisfies Record<string, FileValidationRule>;

export const studentProofDocumentTypes = new Set([
  "college_id_card",
  "library_card",
  "bonafide_certificate",
  "admission_proof",
  "fee_receipt"
]);

export function ruleForDocumentType(documentType: string): FileValidationRule {
  return studentProofDocumentTypes.has(documentType) ? uploadRules.studentProof : uploadRules.verificationDocument;
}

export function validateFile(file: File | undefined, rule: FileValidationRule): string | null {
  if (!file) return null;
  const extension = file.name.includes(".") ? `.${file.name.split(".").pop()?.toLowerCase()}` : "";
  if (!rule.extensions.includes(extension) || !rule.mimeTypes.includes(file.type)) {
    return rule.typeMessage;
  }
  if (file.size > rule.maxMb * MB) {
    return `${rule.label} must be under ${rule.maxMb} MB.`;
  }
  return null;
}

export function fileGuidance(rule: FileValidationRule): string {
  return `${rule.typeMessage.replace("Only ", "").replace(" files are allowed.", "")} under ${rule.maxMb} MB`;
}
