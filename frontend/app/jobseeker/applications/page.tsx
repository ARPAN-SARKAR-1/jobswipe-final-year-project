"use client";

import { MessageCircle, Undo2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import ApplicationTimeline from "@/components/ApplicationTimeline";
import StatusBadge from "@/components/StatusBadge";
import { apiFetch } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Application } from "@/types";

export default function MyApplicationsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const router = useRouter();
  const [applications, setApplications] = useState<Application[]>([]);

  const load = () => {
    apiFetch<Application[]>("/applications/my")
      .then(setApplications)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Applications failed"));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

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
        <div className="grid gap-4">
          {applications.map((application) => (
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
    </main>
  );
}
