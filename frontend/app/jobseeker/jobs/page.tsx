"use client";

import { Bookmark, Send } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import ReportModal from "@/components/ReportModal";
import SkillMultiSelect from "@/components/SkillMultiSelect";
import { apiFetch } from "@/lib/api";
import { experienceLevels, jobTypes, workModes } from "@/lib/options";
import { useAuth } from "@/hooks/useAuth";
import type { Job } from "@/types";

export default function JobsListPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [filters, setFilters] = useState({
    jobType: "",
    experienceLevel: "",
    location: "",
    skills: [] as string[],
    workMode: "",
    activeOnly: true
  });

  const load = () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (typeof value === "boolean") params.set(key, String(value));
      else if (Array.isArray(value)) value.forEach((item) => params.append(key, item));
      else if (value) params.set(key, value);
    });
    apiFetch<Job[]>(`/jobs?${params.toString()}`)
      .then(setJobs)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Jobs failed"));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    load();
  };

  const apply = async (jobId: number) => {
    setApplyingJobId(jobId);
    try {
      await apiFetch("/applications", { method: "POST", body: JSON.stringify({ job_id: jobId }) });
      toast.success("Application submitted");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Apply failed");
    } finally {
      setApplyingJobId(null);
    }
  };

  const save = async (jobId: number) => {
    try {
      await apiFetch("/swipes", { method: "POST", body: JSON.stringify({ job_id: jobId, action: "SAVE" }) });
      toast.success("Job saved");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Save failed");
    }
  };

  if (loading) return <main className="page-shell">Loading jobs...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Jobs List" eyebrow="Explore" />
      <form onSubmit={submit} className="panel mb-6 grid gap-3 p-4 md:grid-cols-3 lg:grid-cols-6">
        <select className="field" value={filters.jobType} onChange={(event) => setFilters({ ...filters, jobType: event.target.value })}>
          <option value="">Job type</option>
          {jobTypes.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
        <select className="field" value={filters.experienceLevel} onChange={(event) => setFilters({ ...filters, experienceLevel: event.target.value })}>
          <option value="">Experience</option>
          {experienceLevels.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
        <input className="field" placeholder="Location" value={filters.location} onChange={(event) => setFilters({ ...filters, location: event.target.value })} />
        <select className="field" value={filters.workMode} onChange={(event) => setFilters({ ...filters, workMode: event.target.value })}>
          <option value="">Work mode</option>
          {workModes.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
        <button className="btn-primary" type="submit">
          Filter
        </button>
        <div className="md:col-span-3 lg:col-span-6">
          <SkillMultiSelect label="Filter by skills" selected={filters.skills} onChange={(skills) => setFilters({ ...filters, skills })} />
        </div>
        <label className="flex items-center gap-2 text-sm font-black text-[#526069] md:col-span-3 lg:col-span-6">
          <input type="checkbox" checked={filters.activeOnly} onChange={(event) => setFilters({ ...filters, activeOnly: event.target.checked })} />
          Active jobs only
        </label>
      </form>

      {jobs.length === 0 ? (
        <EmptyState title="No jobs found" text="Adjust filters or return to the swipe feed for active recommendations." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {jobs.map((job) => {
            const alreadyApplied = Boolean(job.existing_application_status);
            return (
            <JobCard
              key={job.id}
              job={job}
              detailsHref={`/jobseeker/jobs/${job.id}`}
              actions={
                <>
                  <ReportModal jobId={job.id} label="Report Job" />
                  <button className="btn-secondary !py-2" onClick={() => save(job.id)} type="button">
                    <Bookmark size={16} />
                    Save
                  </button>
                  <button className="btn-primary !py-2" onClick={() => apply(job.id)} type="button" disabled={alreadyApplied || applyingJobId === job.id}>
                    <Send size={16} />
                    {alreadyApplied ? "Already Applied" : "Apply"}
                  </button>
                </>
              }
            />
            );
          })}
        </div>
      )}
    </main>
  );
}
