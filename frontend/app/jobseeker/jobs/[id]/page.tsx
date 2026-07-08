"use client";

import { Bookmark, Send } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import BondBadge from "@/components/BondBadge";
import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import ReportModal from "@/components/ReportModal";
import ScreeningQuestionsModal, { getScreeningQuestions } from "@/components/ScreeningQuestionsModal";
import { apiFetch } from "@/lib/api";
import { getJobTrustSignal, jobTrustClass } from "@/lib/jobTrust";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Job, JobSeekerProfile } from "@/types";

export default function JobDetailsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const params = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [profile, setProfile] = useState<JobSeekerProfile | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [applying, setApplying] = useState(false);
  const [screeningOpen, setScreeningOpen] = useState(false);

  useEffect(() => {
    if (loading || !params.id) return;
    apiFetch<Job>(`/jobs/${params.id}`)
      .then(setJob)
      .catch(() => setNotFound(true));
    apiFetch<JobSeekerProfile>("/jobseeker/profile").then(setProfile).catch(() => setProfile(null));
  }, [loading, params.id]);

  const beginApply = () => {
    if (!job) return;
    if (profile && profile.profile_completion_percentage !== undefined && profile.profile_completion_percentage < 100) {
      toast.error("Complete your profile before applying to jobs.");
      return;
    }
    if (getScreeningQuestions(job).length > 0) {
      setScreeningOpen(true);
      return;
    }
    void apply([]);
  };

  const apply = async (screeningAnswers: string[] = []) => {
    if (!job) return;
    setApplying(true);
    try {
      await apiFetch("/applications", {
        method: "POST",
        body: JSON.stringify({ job_id: job.id, screening_answers: screeningAnswers })
      });
      toast.success("Application submitted");
      setScreeningOpen(false);
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
  const profileIncomplete = profile && profile.profile_completion_percentage !== undefined && profile.profile_completion_percentage < 100;
  const trustSignal = getJobTrustSignal(job);

  return (
    <main className="page-shell">
      <PageHeader title="Job Details" eyebrow="Opportunity" />
      {profileIncomplete && (
        <div className="panel mb-5 flex flex-col gap-3 border-amber-200 bg-amber-50 p-4 text-amber-900 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-black">Complete your profile before applying to jobs.</p>
            <p className="mt-1 text-sm font-bold">
              Missing: {(profile.missing_profile_fields || []).slice(0, 5).join(", ") || "required profile details"}.
            </p>
          </div>
          <Link className="btn-primary shrink-0 !py-2" href="/jobseeker/settings/profile">
            Complete profile
          </Link>
        </div>
      )}
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
              <button className="btn-primary !py-2" onClick={beginApply} type="button" disabled={Boolean(job.existing_application_status) || applying || Boolean(profileIncomplete)}>
                <Send size={16} />
                {job.existing_application_status ? `Already Applied: ${job.existing_application_status}` : profileIncomplete ? "Complete Profile" : "Apply"}
              </button>
            </>
          }
        />
        <aside className="panel p-5">
          <h2 className="text-xl font-black">Hiring details</h2>
          <div className="mt-4 grid gap-3 text-sm font-bold text-[#526069]">
            <div className={`rounded-lg p-3 ${jobTrustClass(trustSignal.level)}`}>
              <p className="font-black">Job trust score: {trustSignal.label}</p>
              <p className="mt-1 text-xs font-bold leading-5">
                {trustSignal.reasons.length ? `Based on ${trustSignal.reasons.join(", ")}.` : "Some trust signals are still missing."}
              </p>
            </div>
            {trustSignal.salaryWarning && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                Salary transparency warning: {trustSignal.salaryWarning}. Confirm compensation details before sharing sensitive information.
              </div>
            )}
            <p>Deadline: {formatDate(job.deadline)}</p>
            <p>Work mode: {job.work_mode}</p>
            <p>Experience: {job.required_experience_level}</p>
            {job.career_page_url && (
              <div className="rounded-lg border border-teal-100 bg-teal-50 p-3 text-teal-900">
                <p className="font-black">Official career link</p>
                <a className="mt-1 inline-flex break-all text-sm font-black text-teal-700 underline" href={job.career_page_url} target="_blank" rel="noreferrer">
                  {job.career_page_url}
                </a>
                <p className="mt-2 text-xs font-bold text-teal-800">
                  Always verify the official career link before sharing sensitive personal information.
                </p>
              </div>
            )}
            {job.career_link_status === "LINK_SUSPICIOUS" && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                {job.career_link_warning || "Verify this link before sharing personal information."}
              </div>
            )}
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
      <ScreeningQuestionsModal
        job={job}
        open={screeningOpen}
        submitting={applying}
        onCancel={() => setScreeningOpen(false)}
        onSubmit={(answers) => void apply(answers)}
      />
    </main>
  );
}
