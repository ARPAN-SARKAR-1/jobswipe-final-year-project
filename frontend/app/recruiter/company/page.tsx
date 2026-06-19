"use client";

import { Loader2, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import FileUploadField from "@/components/FileUploadField";
import PageHeader from "@/components/PageHeader";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl } from "@/lib/api";
import { uploadRules, validateFile } from "@/lib/fileValidation";
import { companyTypes } from "@/lib/options";
import { useAuth } from "@/hooks/useAuth";
import type { CompanyProfile, CompanyTestimonial, CompanyType } from "@/types";

export default function CompanyProfilePage() {
  const { loading } = useAuth(["RECRUITER"]);
  const [company, setCompany] = useState<CompanyProfile | null>(null);
  const [testimonials, setTestimonials] = useState<CompanyTestimonial[]>([]);
  const [saving, setSaving] = useState(false);
  const [savingTestimonial, setSavingTestimonial] = useState(false);
  const [form, setForm] = useState({
    company_name: "",
    website: "",
    industry: "",
    company_size: "",
    employee_count_estimate: "",
    headquarters: "",
    founded_year: "",
    company_type: "OTHER" as CompanyType,
    description: "",
    location: "",
    career_page_url: "",
    linkedin_url: "",
    glassdoor_url: "",
    ambitionbox_url: "",
    about_company: "",
    culture_summary: "",
    benefits: "",
    hiring_process: "",
    work_mode: "",
    official_email_domain: "",
    designation: "",
    work_email: ""
  });
  const [testimonialForm, setTestimonialForm] = useState({
    title: "",
    statement: "",
    reviewer_label: "",
    rating: "",
    visibility: "PUBLIC"
  });

  const load = () => {
    apiFetch<CompanyProfile>("/recruiter/company-profile")
      .then((data) => {
        setCompany(data);
        setForm({
          company_name: data.company_name || "",
          website: data.website || "",
          industry: data.industry || "",
          company_size: data.company_size || "",
          employee_count_estimate: data.employee_count_estimate ? String(data.employee_count_estimate) : "",
          headquarters: data.headquarters || "",
          founded_year: data.founded_year ? String(data.founded_year) : "",
          company_type: data.company_type || "OTHER",
          description: data.description || "",
          location: data.location || "",
          career_page_url: data.career_page_url || "",
          linkedin_url: data.linkedin_url || "",
          glassdoor_url: data.glassdoor_url || "",
          ambitionbox_url: data.ambitionbox_url || "",
          about_company: data.about_company || "",
          culture_summary: data.culture_summary || "",
          benefits: data.benefits || "",
          hiring_process: data.hiring_process || "",
          work_mode: data.work_mode || "",
          official_email_domain: data.official_email_domain || "",
          designation: data.designation || "",
          work_email: data.work_email || ""
        });
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Company profile failed"));
    apiFetch<CompanyTestimonial[]>("/recruiter/company-testimonials")
      .then(setTestimonials)
      .catch(() => setTestimonials([]));
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
          employee_count_estimate: form.employee_count_estimate ? Number(form.employee_count_estimate) : null,
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

  const submitTestimonial = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSavingTestimonial(true);
    try {
      const created = await apiFetch<CompanyTestimonial>("/recruiter/company-testimonials", {
        method: "POST",
        body: JSON.stringify({
          ...testimonialForm,
          rating: testimonialForm.rating ? Number(testimonialForm.rating) : null
        })
      });
      setTestimonials([created, ...testimonials]);
      setTestimonialForm({ title: "", statement: "", reviewer_label: "", rating: "", visibility: "PUBLIC" });
      toast.success("Company testimonial submitted for admin review");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Testimonial save failed");
    } finally {
      setSavingTestimonial(false);
    }
  };

  const uploadLogo = async (file: File | undefined) => {
    if (!file) return;
    const validationError = validateFile(file, uploadRules.companyLogo);
    if (validationError) return toast.error(validationError);
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
            <div className="flex flex-wrap justify-center gap-2">
              <VerificationStatusBadge status={company.verification_status} />
              <VerificationStatusBadge status={company.recruiter_verification_status} />
            </div>
          </div>
          {company.verification_note && <p className="mt-3 text-sm font-bold leading-6 text-[#6b767d]">{company.verification_note}</p>}
          <div className="mt-5 rounded-lg bg-[#fbfaf7] p-3 text-left">
            <p className="text-sm font-black text-[#172026]">Company completion: {company.company_completion_percentage || 0}%</p>
            <div className="mt-2 h-2 rounded-lg bg-stone-200">
              <div className="h-2 rounded-lg bg-teal-600" style={{ width: `${company.company_completion_percentage || 0}%` }} />
            </div>
            {company.missing_company_fields && company.missing_company_fields.length > 0 && (
              <p className="mt-2 text-xs font-bold leading-5 text-amber-700">
                Missing: {company.missing_company_fields.join(", ")}
              </p>
            )}
          </div>
          <FileUploadField
            className="mt-5 text-left"
            label="Company logo"
            buttonLabel="Upload company logo"
            rule={uploadRules.companyLogo}
            onValidFile={uploadLogo}
          />
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
            <div>
              <label className="label" htmlFor="industry">
                Industry
              </label>
              <input id="industry" className="field" value={form.industry} onChange={(event) => setForm({ ...form, industry: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="company_size">
                Company size
              </label>
              <select id="company_size" className="field" value={form.company_size} onChange={(event) => setForm({ ...form, company_size: event.target.value })}>
                <option value="">Select size</option>
                {["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5000+"].map((size) => (
                  <option key={size}>{size}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="headquarters">
                Headquarters
              </label>
              <input id="headquarters" className="field" value={form.headquarters} onChange={(event) => setForm({ ...form, headquarters: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="career_page_url">
                Official career page URL
              </label>
              <input id="career_page_url" className="field" type="url" value={form.career_page_url} onChange={(event) => setForm({ ...form, career_page_url: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="employee_count_estimate">
                Employee count estimate
              </label>
              <input id="employee_count_estimate" className="field" type="number" value={form.employee_count_estimate} onChange={(event) => setForm({ ...form, employee_count_estimate: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="founded_year">
                Founded year
              </label>
              <input id="founded_year" className="field" type="number" value={form.founded_year} onChange={(event) => setForm({ ...form, founded_year: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="company_type">
                Company type
              </label>
              <select id="company_type" className="field" value={form.company_type} onChange={(event) => setForm({ ...form, company_type: event.target.value as CompanyType })}>
                {companyTypes.map((type) => (
                  <option key={type} value={type}>
                    {type.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="official_email_domain">
                Official email domain
              </label>
              <input id="official_email_domain" className="field" value={form.official_email_domain} onChange={(event) => setForm({ ...form, official_email_domain: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="work_email">
                Recruiter work email
              </label>
              <input id="work_email" className="field" type="email" value={form.work_email} onChange={(event) => setForm({ ...form, work_email: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="designation">
                Designation
              </label>
              <input id="designation" className="field" value={form.designation} onChange={(event) => setForm({ ...form, designation: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="work_mode">
                Work mode
              </label>
              <select id="work_mode" className="field" value={form.work_mode} onChange={(event) => setForm({ ...form, work_mode: event.target.value })}>
                <option value="">Select work mode</option>
                {["Remote", "Hybrid", "On-site", "Flexible"].map((mode) => (
                  <option key={mode}>{mode}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="label" htmlFor="description">
              Description
            </label>
            <textarea id="description" className="field min-h-36" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="about_company">
              About company
            </label>
            <textarea id="about_company" className="field min-h-28" value={form.about_company} onChange={(event) => setForm({ ...form, about_company: event.target.value })} />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Textarea label="Culture summary" value={form.culture_summary} onChange={(value) => setForm({ ...form, culture_summary: value })} />
            <Textarea label="Benefits" value={form.benefits} onChange={(value) => setForm({ ...form, benefits: value })} />
            <Textarea label="Hiring process" value={form.hiring_process} onChange={(value) => setForm({ ...form, hiring_process: value })} />
            <div className="grid gap-4">
              <UrlInput label="LinkedIn URL" value={form.linkedin_url} onChange={(value) => setForm({ ...form, linkedin_url: value })} />
              <UrlInput label="Glassdoor URL (external reference only)" value={form.glassdoor_url} onChange={(value) => setForm({ ...form, glassdoor_url: value })} />
              <UrlInput label="AmbitionBox URL (external reference only)" value={form.ambitionbox_url} onChange={(value) => setForm({ ...form, ambitionbox_url: value })} />
            </div>
          </div>
          <p className="rounded-lg bg-teal-50 p-3 text-sm font-bold text-teal-900">
            Company details and official career links help protect users from fake job posts. External review links are references only; do not copy third-party reviews into Swipe for Success.
          </p>
          <button className="btn-primary" disabled={saving} type="submit">
            {saving && <Loader2 className="animate-spin" size={18} />}
            Save/update company profile
          </button>
        </form>
      </div>
      <section className="panel mt-5 p-5">
        <h2 className="text-xl font-black">Company-provided testimonials</h2>
        <p className="mt-2 text-sm font-bold leading-6 text-[#6b767d]">
          Add first-party highlights only. Public testimonials are labeled as company-provided and shown after admin approval.
        </p>
        <form onSubmit={submitTestimonial} className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label className="label" htmlFor="testimonial_title">Title</label>
            <input id="testimonial_title" className="field" required value={testimonialForm.title} onChange={(event) => setTestimonialForm({ ...testimonialForm, title: event.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="testimonial_label">Reviewer label optional</label>
            <input id="testimonial_label" className="field" value={testimonialForm.reviewer_label} onChange={(event) => setTestimonialForm({ ...testimonialForm, reviewer_label: event.target.value })} placeholder="Employee feedback, HR team, Intern experience" />
          </div>
          <div>
            <label className="label" htmlFor="testimonial_rating">Rating optional</label>
            <input id="testimonial_rating" className="field" type="number" min="1" max="5" value={testimonialForm.rating} onChange={(event) => setTestimonialForm({ ...testimonialForm, rating: event.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="testimonial_visibility">Visibility</label>
            <select id="testimonial_visibility" className="field" value={testimonialForm.visibility} onChange={(event) => setTestimonialForm({ ...testimonialForm, visibility: event.target.value })}>
              <option value="PUBLIC">Public after approval</option>
              <option value="PRIVATE">Private</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="label" htmlFor="testimonial_statement">Statement</label>
            <textarea id="testimonial_statement" className="field min-h-28" required value={testimonialForm.statement} onChange={(event) => setTestimonialForm({ ...testimonialForm, statement: event.target.value })} />
          </div>
          <button className="btn-primary md:col-span-2" disabled={savingTestimonial} type="submit">
            {savingTestimonial && <Loader2 className="animate-spin" size={18} />}
            Submit testimonial for review
          </button>
        </form>
        <div className="mt-5 grid gap-3">
          {testimonials.map((item) => (
            <div key={item.id} className="rounded-lg border border-black/10 bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-black">{item.title}</p>
                <span className="rounded-lg bg-[#fbfaf7] px-2.5 py-1 text-xs font-black text-[#526069]">{item.status.replaceAll("_", " ")}</span>
              </div>
              <p className="mt-2 text-sm font-bold leading-6 text-[#526069]">{item.statement}</p>
              <p className="mt-2 text-xs font-black text-teal-700">Company-provided testimonial</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

function Textarea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  const id = label.toLowerCase().replaceAll(" ", "_");
  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      <textarea id={id} className="field min-h-28" value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function UrlInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  const id = label.toLowerCase().replaceAll(" ", "_");
  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      <input id={id} className="field" type="url" value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
