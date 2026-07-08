"use client";

import { BriefcaseBusiness, CalendarX, ClipboardList, PlusCircle, Radio, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import StatCard from "@/components/StatCard";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { CompanyProfile, Job } from "@/types";

type RecruiterDashboard = {
  total_jobs: number;
  active_jobs: number;
  expired_jobs: number;
  applications_received: number;
  posted_jobs: Job[];
  company_profile: CompanyProfile;
};

export default function RecruiterDashboardPage() {
  const { loading } = useAuth(["RECRUITER"]);
  const [data, setData] = useState<RecruiterDashboard | null>(null);

  useEffect(() => {
    if (loading) return;
    apiFetch<RecruiterDashboard>("/recruiter/dashboard")
      .then(setData)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Dashboard failed"));
  }, [loading]);

  if (loading || !data) return <main className="page-shell">Loading recruiter dashboard...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Recruiter Dashboard" eyebrow="Hiring">
        <Link href="/recruiter/jobs/new" className="btn-primary">
          <PlusCircle size={18} />
          Post a Job
        </Link>
      </PageHeader>

      <section className="panel mb-6 p-5">
        <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
          <div>
            <h2 className="text-xl font-black">Company verification</h2>
            <p className="mt-1 text-sm font-bold leading-6 text-[#6b767d]">
              {data.company_profile.recruiter_verification_status === "VERIFIED" && (data.company_profile.company_completion_percentage || 0) >= 100
                ? "Your company profile is verified and complete. You can post active jobs."
                : "Your company profile must be verified by admin before posting jobs."}
            </p>
            <div className="mt-3 max-w-xl">
              <div className="flex items-center justify-between gap-3 text-xs font-black text-[#526069]">
                <span>Company completion</span>
                <span>{data.company_profile.company_completion_percentage || 0}%</span>
              </div>
              <div className="mt-1 h-2 rounded-lg bg-stone-200">
                <div className="h-2 rounded-lg bg-teal-600" style={{ width: `${data.company_profile.company_completion_percentage || 0}%` }} />
              </div>
              {data.company_profile.missing_company_fields && data.company_profile.missing_company_fields.length > 0 && (
                <p className="mt-2 text-xs font-bold text-amber-700">Missing: {data.company_profile.missing_company_fields.join(", ")}</p>
              )}
            </div>
            {data.company_profile.verification_note && (
              <p className="mt-2 text-sm font-bold text-[#526069]">{data.company_profile.verification_note}</p>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <VerificationStatusBadge status={data.company_profile.verification_status} />
            <VerificationStatusBadge status={data.company_profile.recruiter_verification_status} />
          </div>
        </div>
        {data.company_profile.missing_company_fields && data.company_profile.missing_company_fields.length > 0 && (
          <Link href="/recruiter/company" className="btn-primary mt-4 inline-flex !py-2">
            Complete company profile
          </Link>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Posted jobs" value={data.total_jobs} icon={BriefcaseBusiness} />
        <StatCard label="Applications received" value={data.applications_received} icon={ClipboardList} />
        <StatCard label="Active jobs" value={data.active_jobs} icon={Radio} />
        <StatCard label="Expired jobs" value={data.expired_jobs} icon={CalendarX} />
      </section>

      <section className="panel mt-6 flex flex-col justify-between gap-4 p-5 sm:flex-row sm:items-center">
        <div className="flex min-w-0 gap-3">
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-teal-50 text-teal-700">
            <Sparkles size={20} />
          </div>
          <div className="min-w-0">
            <h2 className="text-xl font-black">Review candidates with swipe</h2>
            <p className="mt-1 text-sm font-bold leading-6 text-[#6b767d]">
              Quickly shortlist or reject active applicants while keeping the existing chat and application status workflow.
            </p>
          </div>
        </div>
        <Link href="/recruiter/swipe" className="btn-primary shrink-0 !py-2">
          Swipe Candidates
        </Link>
      </section>

      <section className="mt-7">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-black">Manage jobs</h2>
          <Link href="/recruiter/applications" className="btn-secondary !py-2">
            View applications
          </Link>
        </div>
        {data.posted_jobs.length === 0 ? (
          <EmptyState title="No jobs posted" text="Create your first role and start receiving applications from job seekers." />
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {data.posted_jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
