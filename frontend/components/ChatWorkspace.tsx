"use client";

import { Inbox, MessageCircle, Send } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { apiFetch } from "@/lib/api";
import { cx } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { ChatMessage, ChatThread } from "@/types";

export default function ChatWorkspace({ selectedThreadId }: { selectedThreadId?: number }) {
  const { user, loading } = useAuth(["RECRUITER", "JOB_SEEKER"]);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messageText, setMessageText] = useState("");
  const [sending, setSending] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);

  const selectedThread = useMemo(
    () => threads.find((thread) => thread.id === selectedThreadId) || threads[0] || null,
    [threads, selectedThreadId]
  );

  const loadThreads = () => {
    apiFetch<ChatThread[]>("/chats")
      .then(setThreads)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Messages failed"));
  };

  useEffect(() => {
    if (!loading) loadThreads();
  }, [loading]);

  useEffect(() => {
    if (!selectedThread) {
      setMessages([]);
      return;
    }
    setMessagesLoading(true);
    apiFetch<ChatMessage[]>(`/chats/${selectedThread.id}/messages`)
      .then((rows) => {
        setMessages(rows);
        return apiFetch(`/chats/${selectedThread.id}/read`, { method: "PUT" });
      })
      .then(loadThreads)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Chat failed"))
      .finally(() => setMessagesLoading(false));
  }, [selectedThread?.id]);

  const sendMessage = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedThread) return;
    const trimmed = messageText.trim();
    if (!trimmed) {
      toast.error("Message cannot be empty");
      return;
    }
    if (trimmed.length > 1000) {
      toast.error("Message must be 1000 characters or less");
      return;
    }
    setSending(true);
    try {
      const message = await apiFetch<ChatMessage>(`/chats/${selectedThread.id}/messages`, {
        method: "POST",
        body: JSON.stringify({ message_text: trimmed })
      });
      setMessages((rows) => [...rows, message]);
      setMessageText("");
      loadThreads();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Message failed");
    } finally {
      setSending(false);
    }
  };

  if (loading || !user) return <main className="page-shell">Loading messages...</main>;

  const canSend = selectedThread?.status === "ACTIVE" && selectedThread.application_status === "SHORTLISTED";
  const otherName =
    user.role === "RECRUITER"
      ? selectedThread?.job_seeker_name || "Job seeker"
      : selectedThread?.recruiter_name || "Recruiter";

  return (
    <main className="page-shell">
      <div className="mb-6 flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-black uppercase text-teal-700">Controlled communication</p>
          <h1 className="mt-2 text-3xl font-black tracking-normal md:text-4xl">Messages</h1>
        </div>
        <StatusBadge status={user.role} />
      </div>

      {threads.length === 0 ? (
        <EmptyState
          title="No conversations yet"
          text={user.role === "RECRUITER" ? "Shortlist an application and send the first message to start a chat." : "Chats appear after a recruiter shortlists your application and starts the conversation."}
        />
      ) : (
        <section className="panel grid min-h-[680px] overflow-hidden lg:grid-cols-[340px_1fr]">
          <aside className="border-b border-black/5 bg-[#fbfaf7] lg:border-b-0 lg:border-r">
            <div className="flex items-center gap-2 p-4">
              <Inbox size={18} />
              <h2 className="font-black">Conversations</h2>
            </div>
            <div className="grid max-h-[620px] overflow-y-auto">
              {threads.map((thread) => (
                <Link
                  key={thread.id}
                  href={`/messages/${thread.id}`}
                  className={cx(
                    "border-t border-black/5 p-4 transition hover:bg-white",
                    selectedThread?.id === thread.id && "bg-white"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-black text-[#172026]">{thread.job_title || `Job #${thread.job_id}`}</p>
                      <p className="mt-1 text-sm font-bold text-[#6b767d]">{user.role === "RECRUITER" ? thread.job_seeker_name : thread.recruiter_name}</p>
                    </div>
                    {thread.unread_count > 0 && (
                      <span className="rounded-lg bg-rose-50 px-2 py-1 text-xs font-black text-rose-700">{thread.unread_count}</span>
                    )}
                  </div>
                  {thread.last_message && <p className="mt-3 line-clamp-2 text-sm font-bold leading-6 text-[#526069]">{thread.last_message}</p>}
                  <div className="mt-3 flex flex-wrap gap-2">
                    <StatusBadge status={thread.status} />
                    {thread.application_status && <StatusBadge status={thread.application_status} />}
                  </div>
                </Link>
              ))}
            </div>
          </aside>

          <section className="flex min-h-[680px] flex-col">
            {selectedThread ? (
              <>
                <div className="border-b border-black/5 p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-black">{selectedThread.job_title || `Job #${selectedThread.job_id}`}</h2>
                      <p className="mt-1 text-sm font-bold text-[#6b767d]">
                        {selectedThread.company_name || "Company"} · {otherName}
                      </p>
                    </div>
                    <StatusBadge status={selectedThread.status} />
                  </div>
                  {selectedThread.status !== "ACTIVE" && (
                    <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                      This chat is paused or closed and cannot accept new messages.
                    </p>
                  )}
                  {selectedThread.application_status !== "SHORTLISTED" && (
                    <p className="mt-3 rounded-lg border border-stone-200 bg-stone-50 p-3 text-sm font-bold text-stone-700">
                      Chat is only available while the application is shortlisted.
                    </p>
                  )}
                </div>

                <div className="flex-1 space-y-3 overflow-y-auto bg-white/45 p-5">
                  {messagesLoading ? (
                    <p className="text-sm font-bold text-[#6b767d]">Loading conversation...</p>
                  ) : (
                    messages.map((message) => {
                      const mine = message.sender_id === user.id;
                      return (
                        <div key={message.id} className={cx("flex", mine ? "justify-end" : "justify-start")}>
                          <div
                            className={cx(
                              "max-w-[min(680px,82%)] rounded-lg px-4 py-3 shadow-sm",
                              mine ? "bg-[#172026] text-white" : "border border-black/5 bg-white text-[#172026]"
                            )}
                          >
                            <p className="text-sm font-black opacity-80">{mine ? "You" : message.sender_name || otherName}</p>
                            <p className="mt-1 whitespace-pre-wrap text-sm font-semibold leading-6">{message.message_text}</p>
                            <p className={cx("mt-2 text-xs font-bold", mine ? "text-white/60" : "text-[#8a949a]")}>{formatMessageTime(message.created_at)}</p>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                <form onSubmit={sendMessage} className="border-t border-black/5 bg-[#fbfaf7] p-4">
                  <div className="flex flex-col gap-3 md:flex-row">
                    <textarea
                      className="field min-h-24 md:min-h-0"
                      maxLength={1000}
                      placeholder={canSend ? "Write a message..." : "Messaging is unavailable for this chat"}
                      value={messageText}
                      onChange={(event) => setMessageText(event.target.value)}
                      disabled={!canSend || sending}
                    />
                    <button className="btn-primary md:w-36" type="submit" disabled={!canSend || sending}>
                      <Send size={17} />
                      Send
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div className="grid flex-1 place-items-center p-6 text-center">
                <div>
                  <MessageCircle className="mx-auto text-[#8a949a]" size={34} />
                  <h2 className="mt-3 text-xl font-black">Select a conversation</h2>
                </div>
              </div>
            )}
          </section>
        </section>
      )}
    </main>
  );
}

function formatMessageTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
