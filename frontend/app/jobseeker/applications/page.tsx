"use client";

import { MessageCircle, Undo2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import ListToolbar from "@/components/ListToolbar";
import PageHeader from "@/components/PageHeader";
import PaginationControls from "@/components/PaginationControls";
import ApplicationTimeline from "@/components/ApplicationTimeline";
import ApplicationStatusTracker from "@/components/ApplicationStatusTracker";
import StatusBadge from "@/components/StatusBadge";
import { apiFetch } from "@/lib/api";
import { paginateItems, textMatches } from "@/lib/listing";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Application } from "@/types";

export default function MyApplicationsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const router = useRouter();
  const [applications, setApplications] = useState<Application[]>([]);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const load = () => {
    apiFetch<Application[]>("/applications/my")
      .then(setApplications)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Applications failed"));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  useEffect(() => {
    setPage(1);
  }, [query, statusFilter, sort, pageSize]);

  const filteredApplications = useMemo(() => {
    return applications
      .filter((application) =>
        textMatches(application, query, [
          (item) => item.job?.title,
          (item) => item.job?.company_name,
          (item) => item.status,
          (item) => item.admin_status
        ])
      )
      .filter((application) => !statusFilter || application.status === statusFilter)
      .sort((a, b) => {
        if (sort === "oldest") return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        if (sort === "status") return a.status.localeCompare(b.status);
        if (sort === "deadline") return new Date(a.job?.deadline || 0).getTime() - new Date(b.job?.deadline || 0).getTime();
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
  }, [applications, query, statusFilter, sort]);

  const pagedApplications = useMemo(() => paginateItems(filteredApplications, page, pageSize), [filteredApplications, page, pageSize]);

  const withdraw = async (id: number) => {
    try {
      await apiFetch(`/applications/${id}/withdraw`, { method: "PUT" });
      toast.success("Application withdrawn");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Withdraw failed");
    }
  };

  if (loading) return <main className="page-shell">Loading applications...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Applications" eyebrow="History" />
      {applications.length === 0 ? (
        <EmptyState title="No applications yet" text="Swipe right on a job or apply from the jobs list to start tracking applications." />
      ) : (
        <div className="panel overflow-hidden">
          <ListToolbar
            searchValue={query}
            onSearchChange={setQuery}
            searchPlaceholder="Search by job, company, or status"
            filters={[{ label: "Status", value: statusFilter, allLabel: "All statuses", options: ["APPLIED", "VIEWED", "SHORTLISTED", "INTERVIEWED", "HIRED", "REJECTED", "WITHDRAWN"].map((status) => ({ label: status, value: status })), onChange: setStatusFilter }]}
            sortValue={sort}
            sortOptions={[
              { label: "Newest first", value: "newest" },
              { label: "Oldest first", value: "oldest" },
              { label: "Deadline nearest", value: "deadline" },
              { label: "Status", value: "status" }
            ]}
            onSortChange={setSort}
            onReset={() => {
              setQuery("");
              setStatusFilter("");
              setSort("newest");
            }}
            resultCount={filteredApplications.length}
          />
          {filteredApplications.length === 0 ? (
            <div className="p-4 sm:p-5">
              <EmptyState compact title="No results found" text="No results found for the selected filters." />
            </div>
          ) : (
            <div className="grid gap-4 p-4">
          {pagedApplications.map((application) => (
            <div key={application.id} className="panel grid gap-4 p-4 lg:grid-cols-[1fr_260px]">
              {application.job && <JobCard job={application.job} detailsHref={`/jobseeker/jobs/${application.job.id}`} />}
              <div className="rounded-lg bg-[#fbfaf7] p-4">
                <StatusBadge status={application.status} />
                {application.admin_status === "PAUSED" && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                    Application paused by admin{application.admin_note ? `: ${application.admin_note}` : "."}
                  </div>
                )}
                {application.job && application.job.moderation_status !== "ACTIVE" && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                    This job is {application.job.moderation_status.toLowerCase()} by admin.
                  </div>
                )}
                <p className="mt-4 text-sm font-bold text-[#6b767d]">Applied on {formatDate(application.created_at)}</p>
                {(application.resume_pdf_url || application.job) && (
                  <p className="mt-3 rounded-lg border border-teal-100 bg-teal-50 p-3 text-xs font-bold leading-6 text-teal-800">
                    Resume shared with recruiter for this application.
                  </p>
                )}
                <div className="mt-4">
                  <ApplicationStatusTracker application={application} />
                </div>
                <div className="mt-4 rounded-lg border border-black/5 bg-white p-3">
                  {application.chat_thread_id ? (
                    <button className="btn-primary w-full !py-2" type="button" onClick={() => router.push(`/messages/${application.chat_thread_id}`)}>
                      <MessageCircle size={17} />
                      Open Chat
                    </button>
                  ) : application.status === "REJECTED" || application.status === "WITHDRAWN" || application.admin_status === "PAUSED" ? (
                    <p className="text-sm font-bold leading-6 text-[#6b767d]">Chat unavailable</p>
                  ) : (
                    <p className="text-sm font-bold leading-6 text-[#6b767d]">Waiting for recruiter</p>
                  )}
                </div>
                <div className="mt-4">
                  <ApplicationTimeline applicationId={application.id} />
                </div>
                {application.status === "APPLIED" && (
                  <button className="btn-secondary mt-5 w-full border-rose-200 bg-rose-50 text-rose-700" onClick={() => withdraw(application.id)} type="button">
                    <Undo2 size={17} />
                    Withdraw Application
                  </button>
                )}
              </div>
            </div>
          ))}
            </div>
          )}
          <PaginationControls page={page} pageSize={pageSize} total={filteredApplications.length} onPageChange={setPage} onPageSizeChange={setPageSize} />
        </div>
      )}
    </main>
  );
}
