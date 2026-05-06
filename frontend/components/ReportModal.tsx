"use client";

import { Flag, Loader2 } from "lucide-react";
import { FormEvent, useState } from "react";
import toast from "react-hot-toast";

import { apiFetch } from "@/lib/api";

const reportTypes = [
  ["FAKE_JOB", "Fake job"],
  ["ASKING_MONEY", "Asking money"],
  ["MISLEADING_INFO", "Misleading information"],
  ["ABUSIVE", "Abusive"],
  ["SPAM", "Spam"],
  ["OTHER", "Other"]
] as const;

export default function ReportModal({ jobId, recruiterId, label = "Report Job" }: { jobId?: number; recruiterId?: number; label?: string }) {
  const [open, setOpen] = useState(false);
  const [reportType, setReportType] = useState("FAKE_JOB");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (description.trim().length < 10) {
      toast.error("Please add a little more detail");
      return;
    }
    setSubmitting(true);
    try {
      const endpoint = jobId ? `/reports/job/${jobId}` : `/reports/recruiter/${recruiterId}`;
      await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify({ report_type: reportType, description: description.trim() })
      });
      toast.success("Report submitted");
      setDescription("");
      setOpen(false);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Report failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <button className="btn-secondary !py-2 border-amber-200 bg-amber-50 text-amber-800" type="button" onClick={() => setOpen(true)}>
        <Flag size={16} />
        {label}
      </button>
      {open && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4">
          <form onSubmit={submit} className="w-full max-w-lg rounded-lg bg-white p-5 shadow-premium">
            <h2 className="text-xl font-black">{label}</h2>
            <div className="mt-4 grid gap-4">
              <div>
                <label className="label" htmlFor="report_type">
                  Reason
                </label>
                <select id="report_type" className="field" value={reportType} onChange={(event) => setReportType(event.target.value)}>
                  {reportTypes.map(([value, text]) => (
                    <option key={value} value={value}>
                      {text}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label" htmlFor="report_description">
                  Description
                </label>
                <textarea
                  id="report_description"
                  className="field min-h-32"
                  maxLength={1000}
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Describe what looks suspicious or unsafe."
                />
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button className="btn-secondary" type="button" onClick={() => setOpen(false)}>
                Cancel
              </button>
              <button className="btn-primary" type="submit" disabled={submitting}>
                {submitting && <Loader2 className="animate-spin" size={17} />}
                Submit Report
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
