"use client";

import { Bookmark, Send } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import BondBadge from "@/components/BondBadge";
import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import ReportModal from "@/components/ReportModal";
import { apiFetch } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Job } from "@/types";

export default function JobDetailsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const params = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    if (loading || !params.id) return;
    apiFetch<Job>(`/jobs/${params.id}`)
      .then(setJob)
      .catch(() => setNotFound(true));
  }, [loading, params.id]);

  const apply = async () => {
    if (!job) return;
    setApplying(true);
    try {
      await apiFetch("/applications", { method: "POST", body: JSON.stringify({ job_id: job.id }) });
      toast.success("Application submitted");
      setJob({ ...job, existing_application_status: "APPLIED" });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Apply failed");
    } finally {
      setApplying(false);
    }
  };

  const save = async () => {
    if (!job) return;
    try {
      await apiFetch("/swipes", { method: "POST", body: JSON.stringify({ job_id: job.id, action: "SAVE" }) });
      toast.success("Job saved");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Save failed");
    }
  };

  if (loading) return <main className="page-shell">Loading job details...</main>;
  if (notFound) return <main className="page-shell"><EmptyState title="Job unavailable" text="This job may be inactive, paused, removed, or no longer accepting applications." /></main>;
  if (!job) return <main className="page-shell">Loading job details...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Job Details" eyebrow="Opportunity" />
      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <JobCard
          job={job}
          actions={
            <>
              <ReportModal jobId={job.id} label="Report Job" />
              <ReportModal recruiterId={job.recruiter_id} label="Report Recruiter" />
              <button className="btn-secondary !py-2" onClick={save} type="button">
                <Bookmark size={16} />
                Save
              </button>
              <button className="btn-primary !py-2" onClick={apply} type="button" disabled={Boolean(job.existing_application_status) || applying}>
                <Send size={16} />
                {job.existing_application_status ? `Already Applied: ${job.existing_application_status}` : "Apply"}
              </button>
            </>
          }
        />
        <aside className="panel p-5">
          <h2 className="text-xl font-black">Hiring details</h2>
          <div className="mt-4 grid gap-3 text-sm font-bold text-[#526069]">
            <p>Deadline: {formatDate(job.deadline)}</p>
            <p>Work mode: {job.work_mode}</p>
            <p>Experience: {job.required_experience_level}</p>
            <BondBadge job={job} />
            {job.has_bond && job.bond_details && (
              <div className="rounded-lg bg-amber-50 p-3 text-amber-800">
                <p className="font-black">Bond details</p>
                <p className="mt-1 leading-6">{job.bond_details}</p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </main>
  );
}
