"use client";

import { Bookmark, Send } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import ListToolbar from "@/components/ListToolbar";
import PageHeader from "@/components/PageHeader";
import PaginationControls from "@/components/PaginationControls";
import ReportModal from "@/components/ReportModal";
import SkillMultiSelect from "@/components/SkillMultiSelect";
import { apiFetch } from "@/lib/api";
import { paginateItems, textMatches } from "@/lib/listing";
import { experienceLevels, jobTypes, workModes } from "@/lib/options";
import { useAuth } from "@/hooks/useAuth";
import type { Job, JobSeekerProfile } from "@/types";

export default function JobsListPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [profile, setProfile] = useState<JobSeekerProfile | null>(null);
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [trustFilter, setTrustFilter] = useState("");
  const [roleStageFilter, setRoleStageFilter] = useState("");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
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
    apiFetch<JobSeekerProfile>("/jobseeker/profile").then(setProfile).catch(() => setProfile(null));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  useEffect(() => {
    setPage(1);
  }, [query, trustFilter, roleStageFilter, sort, pageSize, jobs.length]);

  const filteredJobs = useMemo(() => {
    return jobs
      .filter((job) =>
        textMatches(job, query, [
          (item) => item.title,
          (item) => item.company_name,
          (item) => item.required_skills,
          (item) => item.location
        ])
      )
      .filter((job) => {
        if (trustFilter === "VERIFIED_COMPANY") return job.company_verified;
        if (trustFilter === "VERIFIED_RECRUITER") return job.recruiter_verified;
        if (trustFilter === "TRUSTED") return job.trusted_posting;
        return true;
      })
      .filter((job) => {
        const searchText = `${job.title} ${job.job_type} ${job.required_experience_level} ${job.description}`.toLowerCase();
        if (roleStageFilter === "INTERNSHIP") return searchText.includes("internship") || searchText.includes("intern ");
        if (roleStageFilter === "FRESHER") return searchText.includes("fresher") || searchText.includes("entry");
        if (roleStageFilter === "EXPERIENCED") return !searchText.includes("internship") && !searchText.includes("fresher") && !searchText.includes("entry");
        return true;
      })
      .sort((a, b) => {
        if (sort === "deadline") return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
        if (sort === "company") return a.company_name.localeCompare(b.company_name);
        if (sort === "match") return Number(b.match_score || 0) - Number(a.match_score || 0);
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
  }, [jobs, query, trustFilter, roleStageFilter, sort]);

  const pagedJobs = useMemo(() => paginateItems(filteredJobs, page, pageSize), [filteredJobs, page, pageSize]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    load();
  };

  const apply = async (jobId: number) => {
    if (profile && profile.profile_completion_percentage !== undefined && profile.profile_completion_percentage < 100) {
      toast.error("Complete your profile before applying to jobs.");
      return;
    }
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
  const profileIncomplete = profile && profile.profile_completion_percentage !== undefined && profile.profile_completion_percentage < 100;

  return (
    <main className="page-shell">
      <PageHeader title="Jobs List" eyebrow="Explore" />
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
        <div className="panel overflow-hidden">
          <ListToolbar
            searchValue={query}
            onSearchChange={setQuery}
            searchPlaceholder="Search by title, company, skills, or location"
            filters={[
              { label: "Trust", value: trustFilter, allLabel: "All jobs", options: [{ label: "Trusted posting", value: "TRUSTED" }, { label: "Verified company", value: "VERIFIED_COMPANY" }, { label: "Verified recruiter", value: "VERIFIED_RECRUITER" }], onChange: setTrustFilter },
              {
                label: "Role stage",
                value: roleStageFilter,
                allLabel: "All role stages",
                options: [
                  { label: "Internship eligible", value: "INTERNSHIP" },
                  { label: "Fresher roles", value: "FRESHER" },
                  { label: "Experienced roles", value: "EXPERIENCED" }
                ],
                onChange: setRoleStageFilter
              }
            ]}
            sortValue={sort}
            sortOptions={[
              { label: "Newest first", value: "newest" },
              { label: "Deadline nearest", value: "deadline" },
              { label: "Company A-Z", value: "company" },
              { label: "Match score", value: "match" }
            ]}
            onSortChange={setSort}
            onReset={() => {
              setQuery("");
              setTrustFilter("");
              setRoleStageFilter("");
              setSort("newest");
            }}
            resultCount={filteredJobs.length}
          />
          {filteredJobs.length === 0 ? (
            <div className="p-4 sm:p-5">
              <EmptyState compact title="No results found" text="No results found for the selected filters." />
            </div>
          ) : (
            <div className="grid gap-4 p-4 lg:grid-cols-2">
          {pagedJobs.map((job) => {
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
                  <button className="btn-primary !py-2" onClick={() => apply(job.id)} type="button" disabled={alreadyApplied || applyingJobId === job.id || Boolean(profileIncomplete)}>
                    <Send size={16} />
                    {alreadyApplied ? "Already Applied" : profileIncomplete ? "Complete Profile" : "Apply"}
                  </button>
                </>
              }
            />
            );
          })}
            </div>
          )}
          <PaginationControls page={page} pageSize={pageSize} total={filteredJobs.length} onPageChange={setPage} onPageSizeChange={setPageSize} />
        </div>
      )}
    </main>
  );
}
