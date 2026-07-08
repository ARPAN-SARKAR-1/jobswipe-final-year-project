"use client";

import { CheckCircle2, Circle, MessageCircle } from "lucide-react";

type TrackerApplication = {
  status: string;
  chat_thread_id?: number | null;
};

const progressOrder = ["APPLIED", "VIEWED", "SHORTLISTED"] as const;

function isStepDone(status: string, step: string, hasChat: boolean) {
  if (step === "CHAT_STARTED") return hasChat;
  if (status === "REJECTED" || status === "WITHDRAWN") return step === "APPLIED";
  if (status === "HIRED" || status === "INTERVIEWED") return true;
  return progressOrder.indexOf(step as (typeof progressOrder)[number]) <= progressOrder.indexOf(status as (typeof progressOrder)[number]);
}

export default function ApplicationStatusTracker({ application }: { application: TrackerApplication }) {
  const hasChat = Boolean(application.chat_thread_id);
  const terminal = application.status === "REJECTED" || application.status === "WITHDRAWN" ? application.status : null;
  const steps = [
    { key: "APPLIED", label: "Applied" },
    { key: "VIEWED", label: "Viewed" },
    { key: "SHORTLISTED", label: "Shortlisted" },
    { key: "CHAT_STARTED", label: "Chat Started" },
    { key: terminal || "FINAL", label: terminal ? terminal[0] + terminal.slice(1).toLowerCase() : "Final Decision" }
  ];

  return (
    <div className="rounded-lg border border-black/5 bg-white p-3">
      <p className="text-xs font-black uppercase text-[#6b767d]">Application tracker</p>
      <div className="mt-3 grid gap-2">
        {steps.map((step) => {
          const done = step.key === "FINAL" ? false : isStepDone(application.status, step.key, hasChat);
          const active = application.status === step.key || (step.key === "CHAT_STARTED" && hasChat) || terminal === step.key;
          return (
            <div key={step.key} className="flex min-w-0 items-center gap-2 text-sm font-bold">
              {done || active ? <CheckCircle2 className="shrink-0 text-teal-600" size={16} /> : step.key === "CHAT_STARTED" ? <MessageCircle className="shrink-0 text-[#9aa3a8]" size={16} /> : <Circle className="shrink-0 text-[#9aa3a8]" size={16} />}
              <span className={done || active ? "text-[#172026]" : "text-[#8a949a]"}>{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
