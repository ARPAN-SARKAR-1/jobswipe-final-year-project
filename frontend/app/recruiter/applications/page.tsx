"use client";

import { ExternalLink, MessageCircle, Send } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent } from "react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import PageHeader from "@/components/PageHeader";
import ApplicationTimeline from "@/components/ApplicationTimeline";
import StatusBadge from "@/components/StatusBadge";
import { apiFetch, assetUrl } from "@/lib/api";
import { recruiterStatuses } from "@/lib/options";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Application, ChatThread } from "@/types";

export default function RecruiterApplicationsPage() {
  const { loading } = useAuth(["RECRUITER"]);
  const router = useRouter();
  const [applications, setApplications] = useState<Application[]>([]);
  const [chatApplication, setChatApplication] = useState<Application | null>(null);
  const [firstMessage, setFirstMessage] = useState("");
  const [chatSubmitting, setChatSubmitting] = useState(false);

  const load = () => {
    apiFetch<Application[]>("/recruiter/applications")
      .then(setApplications)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Applications failed"));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  const updateStatus = async (id: number, status: string) => {
    try {
      await apiFetch(`/recruiter/applications/${id}/status`, { method: "PUT", body: JSON.stringify({ status }) });
      toast.success("Status updated");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Update failed");
    }
  };

  const startChat = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!chatApplication) return;
    const message = firstMessage.trim();
    if (!message) {
      toast.error("Message cannot be empty");
      return;
    }
    if (message.length > 1000) {
      toast.error("Message must be 1000 characters or less");
      return;
    }
    setChatSubmitting(true);
    try {
      const thread = await apiFetch<ChatThread>("/chats/start", {
        method: "POST",
        body: JSON.stringify({ application_id: chatApplication.id, message_text: message })
      });
      toast.success("Chat started");
      setChatApplication(null);
      setFirstMessage("");
      load();
      router.push(`/messages/${thread.id}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Chat failed");
    } finally {
      setChatSubmitting(false);
    }
  };

  if (loading) return <main className="page-shell">Loading applications...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Applications Received" eyebrow="Recruiter" />
      {applications.length === 0 ? (
        <EmptyState title="No applications received" text="Applications will appear here after job seekers apply or swipe right." />
      ) : (
        <div className="grid gap-4">
          {applications.map((application) => (
            <article key={application.id} className="panel grid gap-4 p-5 lg:grid-cols-[1fr_260px]">
              <div>
                <div className="mb-3 flex flex-wrap items-center gap-3">
                  <StatusBadge status={application.status} />
                  <StatusBadge status={application.admin_status} />
                  <span className="text-sm font-bold text-[#6b767d]">{formatDate(application.created_at)}</span>
                </div>
                <h2 className="text-xl font-black">{application.applicant_name}</h2>
                <p className="mt-1 text-sm font-bold text-[#6b767d]">{application.applicant_email}</p>
                <p className="mt-4 text-base font-black text-[#172026]">{application.job_title}</p>
                {application.admin_status === "PAUSED" && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                    Application paused by admin{application.admin_note ? `: ${application.admin_note}` : "."}
                  </div>
                )}
                {application.job && application.job.moderation_status !== "ACTIVE" && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                    Job {application.job.moderation_status.toLowerCase()} by admin{application.job.moderation_reason ? `: ${application.job.moderation_reason}` : "."}
                  </div>
                )}
                <div className="mt-4 flex flex-wrap gap-3">
                  <ApplicationTimeline applicationId={application.id} />
                  {application.applicant_github_url && (
                    <a className="btn-secondary !py-2" href={application.applicant_github_url} target="_blank">
                      <ExternalLink size={16} />
                      GitHub
                    </a>
                  )}
                  {application.applicant_resume_pdf_url && (
                    <a className="btn-secondary !py-2" href={assetUrl(application.applicant_resume_pdf_url)} target="_blank">
                      <ExternalLink size={16} />
                      Resume PDF
                    </a>
                  )}
                </div>
              </div>
              <div className="rounded-lg bg-[#fbfaf7] p-4">
                <div className="mb-4 rounded-lg border border-black/5 bg-white p-3">
                  {application.chat_thread_id ? (
                    <button className="btn-primary w-full !py-2" type="button" onClick={() => router.push(`/messages/${application.chat_thread_id}`)}>
                      <MessageCircle size={17} />
                      Open Chat
                    </button>
                  ) : application.status === "SHORTLISTED" && application.admin_status === "ACTIVE" && application.job?.moderation_status === "ACTIVE" ? (
                    <button className="btn-primary w-full !py-2" type="button" onClick={() => setChatApplication(application)}>
                      <MessageCircle size={17} />
                      Start Chat
                    </button>
                  ) : application.status === "APPLIED" || application.status === "VIEWED" ? (
                    <p className="text-sm font-bold leading-6 text-[#6b767d]">Shortlist this application to start a controlled chat.</p>
                  ) : (
                    <p className="text-sm font-bold leading-6 text-[#6b767d]">Chat unavailable</p>
                  )}
                </div>
                {application.status === "WITHDRAWN" ? (
                  <div className="rounded-lg border border-stone-200 bg-white p-3 text-sm font-bold leading-6 text-[#526069]">
                    This application was withdrawn by the job seeker and can no longer be updated.
                  </div>
                ) : (
                  <>
                    <label className="label">Update status</label>
                    <select className="field" value={application.status} onChange={(event) => updateStatus(application.id, event.target.value)}>
                      <option value={application.status}>{application.status}</option>
                      {recruiterStatuses.map((status) => (
                        <option key={status}>{status}</option>
                      ))}
                    </select>
                  </>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      {chatApplication && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4">
          <form onSubmit={startChat} className="w-full max-w-lg rounded-lg bg-white p-5 shadow-premium">
            <h2 className="text-xl font-black">Start Chat</h2>
            <p className="mt-2 text-sm font-bold leading-6 text-[#6b767d]">
              Send the first message to {chatApplication.applicant_name}. The job seeker can reply after this.
            </p>
            <div className="mt-4">
              <label className="label" htmlFor="first-chat-message">
                First message
              </label>
              <textarea
                id="first-chat-message"
                className="field min-h-32"
                maxLength={1000}
                value={firstMessage}
                onChange={(event) => setFirstMessage(event.target.value)}
                placeholder="Hi, your application has been shortlisted..."
                required
              />
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button className="btn-secondary" type="button" onClick={() => setChatApplication(null)}>
                Cancel
              </button>
              <button className="btn-primary" type="submit" disabled={chatSubmitting}>
                <Send size={17} />
                Send first message
              </button>
            </div>
          </form>
        </div>
      )}
    </main>
  );
}
