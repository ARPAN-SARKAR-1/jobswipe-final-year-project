"use client";

import { Loader2, Mail, TicketCheck } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import CaptchaBox, { type CaptchaValue } from "@/components/CaptchaBox";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { createSupportTicket, getStoredUser } from "@/lib/api";
import type { SupportTicket, SupportTicketCategory, SupportTicketPriority, SupportTicketRoleType } from "@/types";

const SUPPORT_EMAIL = "swipeforsuccess.support@gmail.com";
const ADMIN_EMAIL = "admin.swipeforsuccess@gmail.com";

function formatSubmittedAt(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

const roleOptions: Array<{ label: string; value: SupportTicketRoleType }> = [
  { label: "Job Seeker", value: "JOB_SEEKER" },
  { label: "Recruiter", value: "RECRUITER" },
  { label: "Admin/Owner", value: "ADMIN_OWNER" },
  { label: "Visitor", value: "VISITOR" }
];

const categoryOptions: Array<{ label: string; value: SupportTicketCategory }> = [
  { label: "Account/Login issue", value: "ACCOUNT_LOGIN" },
  { label: "OTP/Email verification", value: "OTP_EMAIL_VERIFICATION" },
  { label: "Job application issue", value: "JOB_APPLICATION" },
  { label: "Recruiter/company verification", value: "RECRUITER_COMPANY_VERIFICATION" },
  { label: "Profile/document upload", value: "PROFILE_DOCUMENT_UPLOAD" },
  { label: "Bug report", value: "BUG_REPORT" },
  { label: "Privacy/data request", value: "PRIVACY_DATA_REQUEST" },
  { label: "Other", value: "OTHER" }
];

const priorityOptions: Array<{ label: string; value: SupportTicketPriority }> = [
  { label: "Low", value: "LOW" },
  { label: "Medium", value: "MEDIUM" },
  { label: "High", value: "HIGH" }
];

export default function ContactPage() {
  const [captcha, setCaptcha] = useState<CaptchaValue>({ challengeId: "", answer: "" });
  const [loading, setLoading] = useState(false);
  const [createdTicket, setCreatedTicket] = useState<SupportTicket | null>(null);
  const [form, setForm] = useState({
    name: "",
    email: "",
    role_type: "VISITOR" as SupportTicketRoleType,
    category: "ACCOUNT_LOGIN" as SupportTicketCategory,
    priority: "MEDIUM" as SupportTicketPriority,
    subject: "",
    message: ""
  });

  useEffect(() => {
    const user = getStoredUser();
    if (!user) return;
    setForm((current) => ({
      ...current,
      name: current.name || user.name,
      email: current.email || user.email,
      role_type: user.role === "JOB_SEEKER" || user.role === "RECRUITER" ? user.role : "ADMIN_OWNER"
    }));
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    try {
      const ticket = await createSupportTicket({
        ...form,
        captcha_challenge_id: captcha.challengeId,
        captcha_answer: captcha.answer
      });
      setCreatedTicket(ticket);
      toast.success(ticket.email_warning || "Your ticket has been created successfully.");
      setForm((current) => ({ ...current, subject: "", message: "" }));
      setCaptcha({ challengeId: "", answer: "" });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not submit support ticket");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <PageHeader title="Contact Support" eyebrow="Support desk">
        <Link href="/" className="btn-secondary !py-2">
          Home
        </Link>
      </PageHeader>

      <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="panel p-6">
          <h2 className="text-2xl font-black tracking-normal">Need help?</h2>
          <p className="mt-3 text-sm font-bold leading-6 text-[#6b767d]">
            Need help with your account, verification, job application, recruiter access, or platform issue? Raise a support ticket and our team will review it.
          </p>
          <div className="mt-6 grid gap-3">
            <a href={`mailto:${SUPPORT_EMAIL}`} className="rounded-lg border border-black/10 bg-white/80 p-4 text-sm font-bold text-[#526069] transition hover:border-teal-600">
              <span className="flex items-center gap-2 text-[#172026]">
                <Mail size={17} />
                Support
              </span>
              <span className="mt-1 block break-all text-teal-700">{SUPPORT_EMAIL}</span>
            </a>
            <a href={`mailto:${ADMIN_EMAIL}`} className="rounded-lg border border-black/10 bg-white/80 p-4 text-sm font-bold text-[#526069] transition hover:border-teal-600">
              <span className="flex items-center gap-2 text-[#172026]">
                <Mail size={17} />
                Admin
              </span>
              <span className="mt-1 block break-all text-teal-700">{ADMIN_EMAIL}</span>
            </a>
          </div>
          {createdTicket && (
            <div className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
              <div className="flex items-center gap-2 text-emerald-800">
                <TicketCheck size={18} />
                <p className="font-black">Your ticket has been created successfully.</p>
              </div>
              <dl className="mt-3 grid gap-2 text-sm font-bold text-[#526069]">
                <div className="flex flex-wrap justify-between gap-2">
                  <dt>Ticket number</dt>
                  <dd className="font-black text-[#172026]">{createdTicket.ticket_code}</dd>
                </div>
                <div className="flex flex-wrap justify-between gap-2">
                  <dt>Submitted</dt>
                  <dd>{formatSubmittedAt(createdTicket.created_at)}</dd>
                </div>
                <div className="flex flex-wrap justify-between gap-2">
                  <dt>Status</dt>
                  <dd>
                    <StatusBadge status={createdTicket.status} />
                  </dd>
                </div>
              </dl>
              {createdTicket.email_warning && <p className="mt-3 text-sm font-bold text-amber-800">{createdTicket.email_warning}</p>}
            </div>
          )}
        </div>

        <form onSubmit={submit} className="panel p-6">
          <h2 className="text-xl font-black">Submit ticket</h2>
          <div className="mt-5 grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} required />
              <Input label="Email" type="email" value={form.email} onChange={(value) => setForm({ ...form, email: value })} required />
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <Select label="Role / account type" value={form.role_type} options={roleOptions} onChange={(value) => setForm({ ...form, role_type: value as SupportTicketRoleType })} />
              <Select label="Category" value={form.category} options={categoryOptions} onChange={(value) => setForm({ ...form, category: value as SupportTicketCategory })} />
              <Select label="Priority" value={form.priority} options={priorityOptions} onChange={(value) => setForm({ ...form, priority: value as SupportTicketPriority })} />
            </div>
            <Input label="Subject" value={form.subject} onChange={(value) => setForm({ ...form, subject: value })} required minLength={5} maxLength={150} />
            <div>
              <label className="label" htmlFor="message">
                Message
              </label>
              <textarea
                id="message"
                className="field min-h-36"
                maxLength={2000}
                minLength={10}
                required
                value={form.message}
                onChange={(event) => setForm({ ...form, message: event.target.value })}
              />
            </div>
            <CaptchaBox disabled={loading} onChange={setCaptcha} purpose="contact" />
            <button className="btn-primary" disabled={loading} type="submit">
              {loading && <Loader2 className="animate-spin" size={18} />}
              Submit ticket
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

function Input({
  label,
  value,
  onChange,
  required,
  type = "text",
  minLength,
  maxLength
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: string;
  minLength?: number;
  maxLength?: number;
}) {
  const id = label.toLowerCase().replaceAll(" ", "-").replaceAll("/", "-");
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        className="field"
        maxLength={maxLength}
        minLength={minLength}
        required={required}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function Select<T extends string>({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: T;
  options: Array<{ label: string; value: T }>;
  onChange: (value: T) => void;
}) {
  const id = label.toLowerCase().replaceAll(" ", "-").replaceAll("/", "-");
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      <select id={id} className="field" value={value} onChange={(event) => onChange(event.target.value as T)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
