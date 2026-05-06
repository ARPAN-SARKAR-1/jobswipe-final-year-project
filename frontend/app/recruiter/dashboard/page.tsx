"use client";

import { BriefcaseBusiness, CalendarX, ClipboardList, PlusCircle, Radio } from "lucide-react";
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
              {data.company_profile.recruiter_verification_status === "VERIFIED"
                ? "Your company profile is verified. You can post active jobs."
                : "Your company profile must be verified by admin before posting jobs."}
            </p>
            {data.company_profile.verification_note && (
              <p className="mt-2 text-sm font-bold text-[#526069]">{data.company_profile.verification_note}</p>
            )}
          </div>
          <VerificationStatusBadge status={data.company_profile.recruiter_verification_status} />
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Posted jobs" value={data.total_jobs} icon={BriefcaseBusiness} />
        <StatCard label="Applications received" value={data.applications_received} icon={ClipboardList} />
        <StatCard label="Active jobs" value={data.active_jobs} icon={Radio} />
        <StatCard label="Expired jobs" value={data.expired_jobs} icon={CalendarX} />
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
