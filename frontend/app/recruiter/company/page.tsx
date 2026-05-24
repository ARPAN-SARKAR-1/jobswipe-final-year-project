"use client";

import { Loader2, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import BlueTick from "@/components/BlueTick";
import PageHeader from "@/components/PageHeader";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl } from "@/lib/api";
import { companyTypes } from "@/lib/options";
import { uploadRules, validateUploadFile } from "@/lib/uploadValidation";
import { useAuth } from "@/hooks/useAuth";
import type { CompanyProfile, CompanyType } from "@/types";

const emptyForm = {
  company_name: "",
  company_type: "Other" as CompanyType,
  industry: "",
  website: "",
  official_email_domain: "",
  description: "",
  headquarters_location: "",
  founded_year: "",
  company_size: "",
  registration_number: "",
  designation: "",
  department: "",
  official_email: ""
};

export default function CompanyProfilePage() {
  const { loading } = useAuth(["RECRUITER"]);
  const [company, setCompany] = useState<CompanyProfile | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(emptyForm);

  const load = () => {
    apiFetch<CompanyProfile>("/recruiter/company-profile")
      .then((data) => {
        setCompany(data);
        setForm({
          company_name: data.company_name || "",
          company_type: data.company_type || "Other",
          industry: data.industry || "",
          website: data.website || "",
          official_email_domain: data.official_email_domain || "",
          description: data.description || "",
          headquarters_location: data.headquarters_location || data.location || "",
          founded_year: data.founded_year ? String(data.founded_year) : "",
          company_size: data.company_size || "",
          registration_number: data.registration_number || "",
          designation: data.designation || "",
          department: data.department || "",
          official_email: data.official_email || ""
        });
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Company profile failed"));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    try {
      const updated = await apiFetch<CompanyProfile>("/recruiter/company-profile", {
        method: "PUT",
        body: JSON.stringify({
          ...form,
          founded_year: form.founded_year ? Number(form.founded_year) : null
        })
      });
      setCompany(updated);
      toast.success("Company profile saved");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const uploadLogo = async (file: File | undefined) => {
    if (!file) return;
    const validationError = validateUploadFile(file, uploadRules.image);
    if (validationError) {
      toast.error(validationError);
      return;
    }
    const body = new FormData();
    body.append("file", file);
    try {
      await apiFetch("/recruiter/company-logo", { method: "POST", body });
      toast.success("Logo uploaded");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Upload failed");
    }
  };

  if (loading || !company) return <main className="page-shell">Loading company profile...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Company Profile" eyebrow="Recruiter" />
      <div className="grid gap-5 lg:grid-cols-[340px_1fr]">
        <aside className="panel p-5 text-center">
          <div className="mx-auto grid h-32 w-32 place-items-center overflow-hidden rounded-lg border border-black/10 bg-white">
            {company.company_logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={assetUrl(company.company_logo_url)} alt={company.company_name || "Company"} className="h-full w-full object-cover" />
            ) : (
              <Upload size={30} />
            )}
          </div>
          <h2 className="mt-4 text-xl font-black">{company.company_name || "Your company"}</h2>
          <div className="mt-3 flex flex-wrap justify-center gap-2">
            {company.verification_status === "VERIFIED" && <BlueTick label="Verified Company" />}
            <VerificationStatusBadge status={company.verification_status} />
            <VerificationStatusBadge status={company.recruiter_verification_status} />
          </div>
          {(company.company_verification_note || company.verification_note) && (
            <p className="mt-3 text-sm font-bold leading-6 text-[#6b767d]">{company.company_verification_note || company.verification_note}</p>
          )}
          <label className="btn-secondary mt-5 w-full cursor-pointer">
            Upload company logo
            <input className="hidden" type="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" onChange={(event) => uploadLogo(event.target.files?.[0])} />
          </label>
          <p className="mt-2 text-xs font-bold text-[#6b767d]">Images: JPG, PNG, WEBP only, max 2 MB.</p>
        </aside>

        <form onSubmit={submit} className="panel grid gap-4 p-5">
          <div>
            <label className="label" htmlFor="company_name">
              Company name
            </label>
            <input id="company_name" className="field" value={form.company_name} onChange={(event) => setForm({ ...form, company_name: event.target.value })} />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="label" htmlFor="company_type">
                Company type
              </label>
              <select id="company_type" className="field" value={form.company_type} onChange={(event) => setForm({ ...form, company_type: event.target.value as CompanyType })}>
                {companyTypes.map((type) => (
                  <option key={type}>{type}</option>
                ))}
              </select>
            </div>
            <Input label="Industry" value={form.industry} onChange={(value) => setForm({ ...form, industry: value })} />
            <div>
              <label className="label" htmlFor="website">
                Website
              </label>
              <input id="website" className="field" value={form.website} onChange={(event) => setForm({ ...form, website: event.target.value })} />
            </div>
            <Input label="Official email domain" value={form.official_email_domain} onChange={(value) => setForm({ ...form, official_email_domain: value })} />
            <Input label="Headquarters location" value={form.headquarters_location} onChange={(value) => setForm({ ...form, headquarters_location: value })} />
            <Input label="Founded year" type="number" value={form.founded_year} onChange={(value) => setForm({ ...form, founded_year: value })} />
            <Input label="Company size" value={form.company_size} onChange={(value) => setForm({ ...form, company_size: value })} />
            <Input label="Registration number" value={form.registration_number} onChange={(value) => setForm({ ...form, registration_number: value })} />
          </div>
          <div>
            <label className="label" htmlFor="description">
              Description
            </label>
            <textarea id="description" className="field min-h-36" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <Input label="Designation" value={form.designation} onChange={(value) => setForm({ ...form, designation: value })} />
            <Input label="Department" value={form.department} onChange={(value) => setForm({ ...form, department: value })} />
            <Input label="Official email" type="email" value={form.official_email} onChange={(value) => setForm({ ...form, official_email: value })} />
          </div>
          <button className="btn-primary" disabled={saving} type="submit">
            {saving && <Loader2 className="animate-spin" size={18} />}
            Save/update company profile
          </button>
        </form>
      </div>
    </main>
  );
}

function Input({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  const id = label.toLowerCase().replaceAll(" ", "-");
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      <input id={id} className="field" type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
