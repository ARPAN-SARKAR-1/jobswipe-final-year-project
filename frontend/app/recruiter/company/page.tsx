"use client";

import { Loader2, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { CompanyProfile } from "@/types";

export default function CompanyProfilePage() {
  const { loading } = useAuth(["RECRUITER"]);
  const [company, setCompany] = useState<CompanyProfile | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ company_name: "", website: "", description: "", location: "" });

  const load = () => {
    apiFetch<CompanyProfile>("/recruiter/company-profile")
      .then((data) => {
        setCompany(data);
        setForm({
          company_name: data.company_name || "",
          website: data.website || "",
          description: data.description || "",
          location: data.location || ""
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
        body: JSON.stringify(form)
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
    if (file.size > 2 * 1024 * 1024) {
      toast.error("Logo must be under 2 MB");
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
          <div className="mt-3">
            <VerificationStatusBadge status={company.recruiter_verification_status} />
          </div>
          {company.verification_note && <p className="mt-3 text-sm font-bold leading-6 text-[#6b767d]">{company.verification_note}</p>}
          <label className="btn-secondary mt-5 w-full cursor-pointer">
            Upload company logo
            <input className="hidden" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => uploadLogo(event.target.files?.[0])} />
          </label>
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
              <label className="label" htmlFor="website">
                Website
              </label>
              <input id="website" className="field" value={form.website} onChange={(event) => setForm({ ...form, website: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="location">
                Location
              </label>
              <input id="location" className="field" value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} />
            </div>
          </div>
          <div>
            <label className="label" htmlFor="description">
              Description
            </label>
            <textarea id="description" className="field min-h-36" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
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
