"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
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
    if (company?.recruiter_verification_status !== "VERIFIED") {
      toast.error("Your company profile must be verified by admin before posting jobs.");
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
            Your company profile must be verified by admin before posting jobs.
          </p>
          <VerificationStatusBadge status={company.recruiter_verification_status} />
        </div>
      </div>
      <form onSubmit={submit} className="panel grid gap-4 p-5 md:grid-cols-2">
        <Input label="Job title" name="title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} required />
        <Input label="Company name" name="company_name" value={form.company_name} onChange={(value) => setForm({ ...form, company_name: value })} required />
        <Input label="Company logo URL optional" name="company_logo_url" value={form.company_logo_url} onChange={(value) => setForm({ ...form, company_logo_url: value })} />
        <Input label="Location" name="location" value={form.location} onChange={(value) => setForm({ ...form, location: value })} required />
        <Select label="Job type" value={form.job_type} options={jobTypes} onChange={(value) => setForm({ ...form, job_type: value })} />
        <Select label="Work mode" value={form.work_mode} options={workModes} onChange={(value) => setForm({ ...form, work_mode: value })} />
        <Input label="Salary/stipend" name="salary" value={form.salary} onChange={(value) => setForm({ ...form, salary: value })} />
        <Select label="Required experience level" value={form.required_experience_level} options={experienceLevels} onChange={(value) => setForm({ ...form, required_experience_level: value })} />
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
          <label className="label" htmlFor="description">
            Description
          </label>
          <textarea id="description" className="field min-h-36" required value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
        </div>
        <div className="md:col-span-2">
          <label className="label" htmlFor="eligibility">
            Eligibility
          </label>
          <textarea id="eligibility" className="field min-h-28" value={form.eligibility} onChange={(event) => setForm({ ...form, eligibility: event.target.value })} />
        </div>
        <Input label="Deadline" name="deadline" value={form.deadline} onChange={(value) => setForm({ ...form, deadline: value })} required type="date" />
        <label className="flex items-center gap-3 rounded-lg border border-black/10 bg-white/70 p-3 text-sm font-black text-[#526069]">
          <input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
          Active job
        </label>
        <button className="btn-primary md:col-span-2" disabled={saving || company.recruiter_verification_status !== "VERIFIED"} type="submit">
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
      <label className="label" htmlFor={name}>
        {label}
      </label>
      <input id={name} className="field" required={required} type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function Select({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <div>
      <label className="label">{label}</label>
      <select className="field" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </div>
  );
}
