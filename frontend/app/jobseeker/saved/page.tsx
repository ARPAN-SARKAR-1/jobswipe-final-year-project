"use client";

import { Send, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import ListToolbar from "@/components/ListToolbar";
import PageHeader from "@/components/PageHeader";
import PaginationControls from "@/components/PaginationControls";
import ReportModal from "@/components/ReportModal";
import { apiFetch } from "@/lib/api";
import { paginateItems, textMatches } from "@/lib/listing";
import { useAuth } from "@/hooks/useAuth";
import type { Swipe } from "@/types";

export default function SavedJobsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [swipes, setSwipes] = useState<Swipe[]>([]);
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [trustFilter, setTrustFilter] = useState("");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const load = () => {
    apiFetch<Swipe[]>("/swipes/history")
      .then(setSwipes)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Saved jobs failed"));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  const saved = useMemo(() => {
    const map = new Map<number, Swipe>();
    swipes.filter((swipe) => swipe.action === "SAVE" && swipe.job).forEach((swipe) => map.set(swipe.job_id, swipe));
    return Array.from(map.values());
  }, [swipes]);

  useEffect(() => {
    setPage(1);
  }, [query, trustFilter, sort, pageSize]);

  const filteredSaved = useMemo(() => {
    return saved
      .filter((swipe) =>
        textMatches(swipe, query, [
          (item) => item.job?.title,
          (item) => item.job?.company_name,
          (item) => item.job?.required_skills,
          (item) => item.job?.location
        ])
      )
      .filter((swipe) => {
        if (trustFilter === "VERIFIED_COMPANY") return Boolean(swipe.job?.company_verified);
        if (trustFilter === "VERIFIED_RECRUITER") return Boolean(swipe.job?.recruiter_verified);
        if (trustFilter === "ACTIVE") return Boolean(swipe.job?.is_active && swipe.job?.moderation_status === "ACTIVE");
        return true;
      })
      .sort((a, b) => {
        if (sort === "deadline") return new Date(a.job?.deadline || 0).getTime() - new Date(b.job?.deadline || 0).getTime();
        if (sort === "company") return String(a.job?.company_name || "").localeCompare(String(b.job?.company_name || ""));
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
  }, [saved, query, trustFilter, sort]);

  const pagedSaved = useMemo(() => paginateItems(filteredSaved, page, pageSize), [filteredSaved, page, pageSize]);

  const unsave = async (jobId: number) => {
    try {
      await apiFetch(`/swipes/saved/${jobId}`, { method: "DELETE" });
      toast.success("Job unsaved");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unsave failed");
    }
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

  if (loading) return <main className="page-shell">Loading saved jobs...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Saved Jobs" eyebrow="Bookmarks" />
      {saved.length === 0 ? (
        <EmptyState title="No saved jobs yet" text="Use the Save action while swiping to build a short list for later." />
      ) : (
        <div className="panel overflow-hidden">
          <ListToolbar
            searchValue={query}
            onSearchChange={setQuery}
            searchPlaceholder="Search saved jobs by title, company, skills, or location"
            filters={[{ label: "Trust", value: trustFilter, allLabel: "All saved jobs", options: [{ label: "Verified company", value: "VERIFIED_COMPANY" }, { label: "Verified recruiter", value: "VERIFIED_RECRUITER" }, { label: "Active jobs", value: "ACTIVE" }], onChange: setTrustFilter }]}
            sortValue={sort}
            sortOptions={[
              { label: "Newest first", value: "newest" },
              { label: "Deadline nearest", value: "deadline" },
              { label: "Company A-Z", value: "company" }
            ]}
            onSortChange={setSort}
            onReset={() => {
              setQuery("");
              setTrustFilter("");
              setSort("newest");
            }}
            resultCount={filteredSaved.length}
          />
          {filteredSaved.length === 0 ? (
            <div className="p-4 sm:p-5">
              <EmptyState compact title="No results found" text="No results found for the selected filters." />
            </div>
          ) : (
            <div className="grid gap-4 p-4 lg:grid-cols-2">
          {pagedSaved.map((swipe) =>
            swipe.job ? (
              <JobCard
                key={swipe.id}
                job={swipe.job}
                detailsHref={`/jobseeker/jobs/${swipe.job_id}`}
                actions={
                  <>
                    <ReportModal jobId={swipe.job_id} label="Report Job" />
                    <button className="btn-secondary !py-2" onClick={() => unsave(swipe.job_id)} type="button">
                      <Trash2 size={16} />
                      Unsave
                    </button>
                    <button className="btn-primary !py-2" onClick={() => apply(swipe.job_id)} type="button" disabled={Boolean(swipe.job.existing_application_status) || applyingJobId === swipe.job_id}>
                      <Send size={16} />
                      {swipe.job.existing_application_status ? "Already Applied" : "Apply"}
                    </button>
                  </>
                }
              />
            ) : null
          )}
            </div>
          )}
          <PaginationControls page={page} pageSize={pageSize} total={filteredSaved.length} onPageChange={setPage} onPageSizeChange={setPageSize} />
        </div>
      )}
    </main>
  );
}
