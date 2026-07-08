"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
import RequiredLabel from "@/components/RequiredLabel";
import SkillMultiSelect from "@/components/SkillMultiSelect";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch } from "@/lib/api";
import { experienceLevels, jobTypes, workModes } from "@/lib/options";
import { useAuth } from "@/hooks/useAuth";
import type { CompanyProfile } from "@/types";

const initial = {
  title: "",
  company_name: "",
  company_logo_url: "",
  location: "",
  job_type: "Internship",
  work_mode: "Hybrid",
  salary: "",
  required_skills: [] as string[],
  required_experience_level: "Fresher",
  description: "",
  eligibility: "",
  screening_questions: [""] as string[],
  career_page_url: "",
  official_apply_url: "",
  source_type: "COMPANY_PORTAL",
  deadline: "",
  is_active: true,
  has_bond: false,
  bond_years: "",
  bond_details: ""
};

export default function PostJobPage() {
  const router = useRouter();
  const { loading } = useAuth(["RECRUITER"]);
  const [form, setForm] = useState(initial);
  const [company, setCompany] = useState<CompanyProfile | null>(null);
  const [saving, setSaving] = useState(false);
  const companyComplete = company?.company_completion_percentage === undefined || company.company_completion_percentage >= 100;
  const canPost = company?.verification_status === "VERIFIED" && company?.recruiter_verification_status === "VERIFIED" && company?.company_join_status === "APPROVED" && companyComplete;
  const validScreeningQuestions = form.screening_questions.map((question) => question.trim()).filter(Boolean);

  useEffect(() => {
    if (loading) return;
    apiFetch<CompanyProfile>("/recruiter/company-profile")
      .then(setCompany)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Company profile failed"));
  }, [loading]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (form.has_bond && !form.bond_years) {
      toast.error("Bond period in years is required");
      return;
    }
    if (form.has_bond && Number(form.bond_years) < 0) {
      toast.error("Bond period cannot be negative");
      return;
    }
    if (!canPost) {
      toast.error(companyComplete ? "Your company and recruiter membership must be verified before posting jobs." : "Complete company profile before posting jobs.");
      return;
    }
    if (!form.career_page_url.trim()) {
      toast.error("Official career page URL is required.");
      return;
    }
    setSaving(true);
    try {
      await apiFetch("/jobs", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          company_logo_url: form.company_logo_url || null,
          eligibility: form.eligibility || null,
          screening_questions: validScreeningQuestions,
          career_page_url: form.career_page_url,
          official_apply_url: form.official_apply_url || null,
          source_type: form.source_type,
          salary: form.salary || null,
          bond_years: form.has_bond ? Number(form.bond_years) : null,
          bond_details: form.has_bond ? form.bond_details || null : null
        })
      });
      toast.success("Job posted");
      router.push("/recruiter/dashboard");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Post failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !company) return <main className="page-shell">Loading post job...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Post Job" eyebrow="Recruiter" />
      <div className="panel mb-5 p-4">
        <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
          <p className="text-sm font-bold leading-6 text-[#526069]">
            Your company and recruiter membership must be verified and the company profile must be complete before posting public jobs.
          </p>
          <div className="flex flex-wrap gap-2">
            <VerificationStatusBadge status={company.verification_status} />
            <VerificationStatusBadge status={company.recruiter_verification_status} />
          </div>
        </div>
        {!companyComplete && (
          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
            Complete company profile before posting jobs. Missing: {(company?.missing_company_fields || []).join(", ") || "required company details"}.
          </div>
        )}
      </div>
      <form onSubmit={submit} className="panel grid gap-4 p-5 md:grid-cols-2">
        <div className="rounded-lg border border-teal-100 bg-teal-50 p-3 text-sm font-bold leading-6 text-teal-900 md:col-span-2">
          Fields marked with <span className="font-black text-rose-600">*</span> are compulsory for publishing a job.
        </div>
        <Input label="Job title" name="title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} required />
        <Input label="Company name" name="company_name" value={form.company_name} onChange={(value) => setForm({ ...form, company_name: value })} required />
        <Input label="Company logo URL optional" name="company_logo_url" value={form.company_logo_url} onChange={(value) => setForm({ ...form, company_logo_url: value })} />
        <Input label="Location" name="location" value={form.location} onChange={(value) => setForm({ ...form, location: value })} required />
        <Select label="Job type" value={form.job_type} options={jobTypes} onChange={(value) => setForm({ ...form, job_type: value })} required />
        <Select label="Work mode" value={form.work_mode} options={workModes} onChange={(value) => setForm({ ...form, work_mode: value })} required />
        <Input label="Salary/stipend" name="salary" value={form.salary} onChange={(value) => setForm({ ...form, salary: value })} />
        <Select label="Required experience level" value={form.required_experience_level} options={experienceLevels} onChange={(value) => setForm({ ...form, required_experience_level: value })} required />
        <div className="md:col-span-2">
          <SkillMultiSelect label="Required skills" selected={form.required_skills} onChange={(skills) => setForm({ ...form, required_skills: skills })} required />
        </div>
        <div className="md:col-span-2 rounded-lg border border-black/10 bg-white/70 p-4">
          <label className="flex items-center gap-3 text-sm font-black text-[#526069]">
            <input type="checkbox" checked={form.has_bond} onChange={(event) => setForm({ ...form, has_bond: event.target.checked, bond_years: event.target.checked ? form.bond_years : "", bond_details: event.target.checked ? form.bond_details : "" })} />
            Does this job have a bond?
          </label>
          {form.has_bond && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Input label="Bond period in years" name="bond_years" value={form.bond_years} onChange={(value) => setForm({ ...form, bond_years: value })} required type="number" />
              <div className="md:col-span-2">
                <label className="label" htmlFor="bond_details">
                  Bond details
                </label>
                <textarea id="bond_details" className="field min-h-28" value={form.bond_details} onChange={(event) => setForm({ ...form, bond_details: event.target.value })} />
              </div>
            </div>
          )}
        </div>
        <div className="md:col-span-2">
          <RequiredLabel label="Description" htmlFor="description" required />
          <textarea id="description" className="field min-h-36" required aria-required value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
        </div>
        <div className="md:col-span-2">
          <label className="label" htmlFor="eligibility">
            Eligibility
          </label>
          <textarea id="eligibility" className="field min-h-28" value={form.eligibility} onChange={(event) => setForm({ ...form, eligibility: event.target.value })} />
        </div>
        <div className="md:col-span-2 rounded-lg border border-violet-100 bg-violet-50/60 p-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-black text-[#172026]">Screening questions</p>
              <p className="mt-1 text-xs font-bold leading-5 text-[#6b767d]">
                Optional. Add up to five quick questions that applicants answer before applying.
              </p>
            </div>
            <button
              className="btn-secondary !py-2"
              type="button"
              onClick={() => setForm({ ...form, screening_questions: [...form.screening_questions, ""] })}
              disabled={form.screening_questions.length >= 5}
            >
              Add question
            </button>
          </div>
          <div className="mt-4 grid gap-3">
            {form.screening_questions.map((question, index) => (
              <div key={index} className="grid gap-2 sm:grid-cols-[1fr_auto]">
                <input
                  className="field"
                  maxLength={240}
                  placeholder={`Screening question ${index + 1}`}
                  value={question}
                  onChange={(event) => {
                    const next = [...form.screening_questions];
                    next[index] = event.target.value;
                    setForm({ ...form, screening_questions: next });
                  }}
                />
                <button
                  className="btn-secondary !py-2"
                  type="button"
                  onClick={() => setForm({ ...form, screening_questions: form.screening_questions.filter((_, itemIndex) => itemIndex !== index) })}
                  disabled={form.screening_questions.length === 1}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
        <Input label="Official career page URL" name="career_page_url" value={form.career_page_url} onChange={(value) => setForm({ ...form, career_page_url: value })} required type="url" />
        <Input label="Official apply URL optional" name="official_apply_url" value={form.official_apply_url} onChange={(value) => setForm({ ...form, official_apply_url: value })} type="url" />
        <div className="md:col-span-2 rounded-lg border border-teal-100 bg-teal-50 p-3 text-sm font-bold text-teal-900">
          Official career links help applicants verify job authenticity. If an ATS link differs from your company domain, Admin review may be recommended.
        </div>
        <Input label="Deadline" name="deadline" value={form.deadline} onChange={(value) => setForm({ ...form, deadline: value })} required type="date" />
        <label className="flex items-center gap-3 rounded-lg border border-black/10 bg-white/70 p-3 text-sm font-black text-[#526069]">
          <input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
          Active job
        </label>
        <button className="btn-primary md:col-span-2" disabled={saving || !canPost} type="submit">
          {saving && <Loader2 className="animate-spin" size={18} />}
          Post job
        </button>
      </form>
    </main>
  );
}

function Input({ label, name, value, onChange, required, type = "text" }: { label: string; name: string; value: string; onChange: (value: string) => void; required?: boolean; type?: string }) {
  return (
    <div>
      <RequiredLabel label={label} htmlFor={name} required={required} />
      <input id={name} className="field" required={required} aria-required={required || undefined} type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function Select({ label, value, options, onChange, required }: { label: string; value: string; options: string[]; onChange: (value: string) => void; required?: boolean }) {
  return (
    <div>
      <RequiredLabel label={label} required={required} />
      <select className="field" value={value} aria-required={required || undefined} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </div>
  );
}
