"use client";

import { KeyRound, Loader2, ShieldCheck, Upload, UsersRound } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import BlueTick from "@/components/BlueTick";
import PageHeader from "@/components/PageHeader";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl } from "@/lib/api";
import { companyTypes } from "@/lib/options";
import { uploadRules, validateUploadFile } from "@/lib/uploadValidation";
import { useAuth } from "@/hooks/useAuth";
import type { CompanyClaim, CompanyMember, CompanyProfile, CompanyType } from "@/types";

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
  const [members, setMembers] = useState<CompanyMember[]>([]);
  const [saving, setSaving] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [claimToken, setClaimToken] = useState("");
  const [claimForm, setClaimForm] = useState({ requested_company_name: "", requested_domain: "", official_email: "" });
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

  const loadMembers = (companyId?: number | null) => {
    if (!companyId) return;
    apiFetch<CompanyMember[]>(`/companies/${companyId}/members`)
      .then(setMembers)
      .catch(() => setMembers([]));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  useEffect(() => {
    if (company?.company_id) loadMembers(company.company_id);
  }, [company?.company_id]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = new URLSearchParams(window.location.search).get("claimToken");
    if (token) setClaimToken(token);
  }, []);

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

  const submitClaim = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setClaiming(true);
    try {
      const claim = await apiFetch<CompanyClaim>("/companies/claim", {
        method: "POST",
        body: JSON.stringify(claimForm)
      });
      toast.success(claim.requires_admin_review ? "Claim created and sent for admin review" : "Claim created. Check backend console for the demo verification link.");
      setClaimForm({ requested_company_name: "", requested_domain: "", official_email: "" });
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Company claim failed");
    } finally {
      setClaiming(false);
    }
  };

  const verifyClaim = async () => {
    const token = claimToken.trim();
    if (!token) {
      toast.error("Enter the claim verification token");
      return;
    }
    try {
      const result = await apiFetch<{ message: string; claim: CompanyClaim }>(`/companies/claim/${token}/verify`, { method: "POST" });
      toast.success(result.message);
      setClaimToken("");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Claim verification failed");
    }
  };

  const approveMember = async (memberId: number) => {
    try {
      await apiFetch(`/companies/members/${memberId}/approve`, { method: "PUT", body: JSON.stringify({ note: "Approved from company dashboard." }) });
      toast.success("Member approved");
      loadMembers(company?.company_id);
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Approval failed");
    }
  };

  const rejectMember = async (memberId: number) => {
    try {
      await apiFetch(`/companies/members/${memberId}/reject`, { method: "PUT", body: JSON.stringify({ note: "Rejected from company dashboard." }) });
      toast.success("Member rejected");
      loadMembers(company?.company_id);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Rejection failed");
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

      <section className="mt-6 grid gap-5 lg:grid-cols-2">
        <form onSubmit={submitClaim} className="panel grid gap-4 p-5">
          <div className="flex items-center gap-3">
            <ShieldCheck className="text-teal-700" size={22} />
            <h2 className="text-xl font-black">Claim Company</h2>
          </div>
          <Input label="Company name to claim" value={claimForm.requested_company_name} onChange={(value) => setClaimForm({ ...claimForm, requested_company_name: value })} />
          <Input label="Company website/domain" value={claimForm.requested_domain} onChange={(value) => setClaimForm({ ...claimForm, requested_domain: value })} />
          <Input label="Official company email" type="email" value={claimForm.official_email} onChange={(value) => setClaimForm({ ...claimForm, official_email: value })} />
          <button className="btn-primary" disabled={claiming} type="submit">
            {claiming && <Loader2 className="animate-spin" size={18} />}
            Request claim verification
          </button>
        </form>

        <div className="panel grid gap-4 p-5">
          <div className="flex items-center gap-3">
            <KeyRound className="text-teal-700" size={22} />
            <h2 className="text-xl font-black">Verify Claim Token</h2>
          </div>
          <Input label="Verification token" value={claimToken} onChange={setClaimToken} />
          <button className="btn-secondary" type="button" onClick={verifyClaim}>
            Verify company claim
          </button>
          <p className="text-sm font-bold leading-6 text-[#6b767d]">Development mode logs the demo token in the backend console. Reserved brand claims still wait for Owner/Admin review.</p>
        </div>
      </section>

      {members.length > 0 && (
        <section className="panel mt-6 overflow-hidden">
          <div className="flex items-center gap-3 p-5">
            <UsersRound className="text-teal-700" size={22} />
            <h2 className="text-xl font-black">Company Members</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
                <tr>
                  <th className="p-4">Member</th>
                  <th className="p-4">Company role</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Note</th>
                  <th className="p-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                  <tr key={member.id} className="border-t border-black/5">
                    <td className="p-4">
                      <p className="font-black">{member.user_name || "Recruiter"}</p>
                      <p className="font-bold text-[#6b767d]">{member.user_email}</p>
                    </td>
                    <td className="p-4 font-black">{member.company_role.replace("COMPANY_", "")}</td>
                    <td className="p-4"><VerificationStatusBadge status={member.verification_status} /></td>
                    <td className="p-4 font-bold text-[#6b767d]">{member.note || "-"}</td>
                    <td className="p-4">
                      {member.verification_status === "PENDING" ? (
                        <div className="flex flex-wrap gap-2">
                          <button className="btn-secondary !py-2" type="button" onClick={() => approveMember(member.id)}>Approve</button>
                          <button className="btn-secondary !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => rejectMember(member.id)}>Reject</button>
                        </div>
                      ) : (
                        <span className="font-bold text-[#6b767d]">Reviewed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
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
