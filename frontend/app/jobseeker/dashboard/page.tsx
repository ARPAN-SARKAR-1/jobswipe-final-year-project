"use client";

import { Bookmark, BriefcaseBusiness, ClipboardList, Gauge, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
import StatCard from "@/components/StatCard";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

type Dashboard = {
  name: string;
  profile_completion: number;
  recommended_jobs_count: number;
  saved_jobs_count: number;
  applications_count: number;
};

export default function JobSeekerDashboard() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [data, setData] = useState<Dashboard | null>(null);

  useEffect(() => {
    if (loading) return;
    apiFetch<Dashboard>("/jobseeker/dashboard")
      .then(setData)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Dashboard failed"));
  }, [loading]);

  if (loading || !data) {
    return <main className="page-shell">Loading dashboard...</main>;
  }

  return (
    <main className="page-shell">
      <PageHeader title={`Welcome, ${data.name}`} eyebrow="Job Seeker">
        <Link href="/jobseeker/swipe" className="btn-primary">
          <Sparkles size={18} />
          Start swiping
        </Link>
      </PageHeader>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Profile completion" value={`${data.profile_completion}%`} icon={Gauge} />
        <StatCard label="Recommended jobs" value={data.recommended_jobs_count} icon={BriefcaseBusiness} />
        <StatCard label="Saved jobs" value={data.saved_jobs_count} icon={Bookmark} />
        <StatCard label="Applications" value={data.applications_count} icon={ClipboardList} />
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="panel p-6">
          <h2 className="text-2xl font-black">Today&apos;s fastest path</h2>
          <p className="mt-3 text-sm font-medium leading-6 text-[#6b767d]">
            Complete your profile, swipe through active jobs, save the interesting ones, and track applications without returning to long job lists.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/jobseeker/profile" className="btn-secondary">
              Update profile
            </Link>
            <Link href="/jobseeker/jobs" className="btn-secondary">
              Browse jobs
            </Link>
          </div>
        </div>
        <div className="panel p-6">
          <h2 className="text-2xl font-black">Profile signal</h2>
          <div className="mt-5 h-3 rounded-lg bg-stone-200">
            <div className="h-3 rounded-lg bg-teal-600" style={{ width: `${data.profile_completion}%` }} />
          </div>
          <p className="mt-4 text-sm font-bold text-[#6b767d]">Recruiters see stronger context when resume, GitHub, skills, and experience are filled.</p>
        </div>
      </section>
    </main>
  );
}
