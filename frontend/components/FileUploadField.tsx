"use client";

import { Loader2, UploadCloud } from "lucide-react";
import { useState } from "react";

import { fileExample, fileGuidance, validateFile, type FileValidationRule } from "@/lib/fileValidation";
import { cx } from "@/lib/utils";

type FileUploadFieldProps = {
  label: string;
  buttonLabel?: string;
  rule: FileValidationRule;
  helper?: string;
  disabled?: boolean;
  className?: string;
  onValidFile: (file: File) => Promise<unknown> | unknown;
};

export default function FileUploadField({
  label,
  buttonLabel = "Choose file",
  rule,
  helper,
  disabled,
  className,
  onValidFile
}: FileUploadFieldProps) {
  const [selectedName, setSelectedName] = useState("");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    const validationError = validateFile(file, rule);
    if (validationError) {
      setSelectedName("");
      setError(validationError);
      setUploaded(false);
      return;
    }
    setSelectedName(file.name);
    setError("");
    setUploaded(false);
    setUploading(true);
    try {
      await onValidFile(file);
      setUploaded(true);
    } catch {
      setUploaded(false);
      setError("Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={cx("min-w-0", className)}>
      <label className="label">{label}</label>
      <label
        className={cx(
          "smooth-button flex min-h-[54px] w-full cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-black/15 bg-white px-4 py-3 text-center text-sm font-black text-[#172026] shadow-sm hover:border-teal-300 hover:bg-teal-50/50",
          disabled && "pointer-events-none cursor-not-allowed opacity-60"
        )}
      >
        {uploading ? <Loader2 className="animate-spin" size={18} /> : <UploadCloud size={18} />}
        <span className="min-w-0 truncate">{uploading ? "Uploading..." : buttonLabel}</span>
        <input
          className="hidden"
          type="file"
          accept={rule.accept}
          disabled={disabled || uploading}
          onChange={(event) => {
            void handleFile(event.target.files?.[0]);
            event.currentTarget.value = "";
          }}
        />
      </label>
      <div className="mt-2 grid gap-1 text-xs font-bold leading-5 text-[#6b767d]">
        <p>{fileGuidance(rule)}</p>
        <p>{fileExample(rule)}</p>
        {helper && <p>{helper}</p>}
        {selectedName && !error && (
          <p className="break-words rounded-lg bg-teal-50 px-2.5 py-1 text-teal-800">Selected: {selectedName}</p>
        )}
        {uploaded && !error && (
          <p className="break-words rounded-lg bg-emerald-50 px-2.5 py-1 text-emerald-700">Uploaded successfully</p>
        )}
        {error && <p className="break-words rounded-lg bg-rose-50 px-2.5 py-1 text-rose-700">{error}</p>}
      </div>
    </div>
  );
}
