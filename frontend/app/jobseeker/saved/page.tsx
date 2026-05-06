"use client";

import { Send, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import ReportModal from "@/components/ReportModal";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { Swipe } from "@/types";

export default function SavedJobsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [swipes, setSwipes] = useState<Swipe[]>([]);
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);

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
        <div className="grid gap-4 lg:grid-cols-2">
          {saved.map((swipe) =>
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
    </main>
  );
}
