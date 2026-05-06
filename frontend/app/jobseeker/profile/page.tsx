"use client";

import { FileText, Loader2, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
import SkillMultiSelect from "@/components/SkillMultiSelect";
import { apiFetch, assetUrl } from "@/lib/api";
import { experienceLevels, jobTypes } from "@/lib/options";
import { splitSkills } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { JobSeekerProfile } from "@/types";

const emptyProfile = {
  phone: "",
  github_url: "",
  education: "",
  degree: "",
  college: "",
  passing_year: "",
  cgpa_or_percentage: "",
  skills: [] as string[],
  experience_level: "Fresher",
  preferred_location: "",
  preferred_job_type: "Full-time"
};

export default function JobSeekerProfilePage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [profile, setProfile] = useState<JobSeekerProfile | null>(null);
  const [form, setForm] = useState(emptyProfile);
  const [saving, setSaving] = useState(false);

  const load = () => {
    apiFetch<JobSeekerProfile>("/jobseeker/profile")
      .then((data) => {
        setProfile(data);
        setForm({
          phone: data.phone || "",
          github_url: data.github_url || "",
          education: data.education || "",
          degree: data.degree || "",
          college: data.college || "",
          passing_year: data.passing_year ? String(data.passing_year) : "",
          cgpa_or_percentage: data.cgpa_or_percentage || "",
          skills: data.skills_list?.length ? data.skills_list : splitSkills(data.skills),
          experience_level: data.experience_level || "Fresher",
          preferred_location: data.preferred_location || "",
          preferred_job_type: data.preferred_job_type || "Full-time"
        });
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Profile failed"));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    try {
      const updated = await apiFetch<JobSeekerProfile>("/jobseeker/profile", {
        method: "PUT",
        body: JSON.stringify({
          ...form,
          passing_year: form.passing_year ? Number(form.passing_year) : null
        })
      });
      setProfile(updated);
      toast.success("Profile saved");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const upload = async (file: File | undefined, endpoint: string, maxBytes: number, pdfOnly = false) => {
    if (!file) return;
    if (file.size > maxBytes) {
      toast.error("File size is too large");
      return;
    }
    if (pdfOnly && file.type !== "application/pdf") {
      toast.error("Resume must be a PDF");
      return;
    }
    const body = new FormData();
    body.append("file", file);
    try {
      await apiFetch<{ url: string; message: string }>(endpoint, { method: "POST", body });
      toast.success("Upload complete");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Upload failed");
    }
  };

  if (loading || !profile) return <main className="page-shell">Loading profile...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Job Seeker Profile" eyebrow="Profile" />
      <div className="grid gap-5 lg:grid-cols-[340px_1fr]">
        <aside className="panel p-5">
          <div className="grid place-items-center text-center">
            <div className="grid h-32 w-32 place-items-center overflow-hidden rounded-lg border border-black/10 bg-white">
              {profile.profile_picture_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={assetUrl(profile.profile_picture_url)} alt={profile.name} className="h-full w-full object-cover" />
              ) : (
                <Upload size={30} />
              )}
            </div>
            <h2 className="mt-4 text-xl font-black">{profile.name}</h2>
            <p className="text-sm font-bold text-[#6b767d]">{profile.email}</p>
          </div>

          <label className="btn-secondary mt-5 w-full cursor-pointer">
            Upload picture
            <input className="hidden" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => upload(event.target.files?.[0], "/jobseeker/profile-picture", 2 * 1024 * 1024)} />
          </label>

          <label className="btn-secondary mt-3 w-full cursor-pointer">
            <FileText size={17} />
            Upload resume PDF
            <input className="hidden" type="file" accept="application/pdf" onChange={(event) => upload(event.target.files?.[0], "/jobseeker/resume", 5 * 1024 * 1024, true)} />
          </label>
          <p className="mt-3 rounded-lg border border-teal-100 bg-teal-50 p-3 text-xs font-bold leading-6 text-teal-800">
            Your resume is not public. It becomes visible only to recruiters when you apply to their job. Owner/Admin may access it only for moderation or support.
          </p>

          {profile.resume_pdf_url && (
            <a className="mt-4 block rounded-lg bg-teal-50 p-3 text-sm font-black text-teal-700" href={assetUrl(profile.resume_pdf_url)} target="_blank">
              View uploaded resume
            </a>
          )}
        </aside>

        <form onSubmit={submit} className="panel grid gap-4 p-5 md:grid-cols-2">
          {[
            ["Phone number", "phone"],
            ["GitHub profile link", "github_url"],
            ["Education", "education"],
            ["Degree", "degree"],
            ["College/university", "college"],
            ["Passing year", "passing_year"],
            ["CGPA/percentage", "cgpa_or_percentage"],
            ["Preferred location", "preferred_location"]
          ].map(([label, key]) => (
            <div key={key}>
              <label className="label" htmlFor={key}>
                {label}
              </label>
              <input id={key} className="field" value={form[key as keyof typeof form] as string} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />
            </div>
          ))}
          <div className="md:col-span-2">
            <SkillMultiSelect label="Skills" selected={form.skills} onChange={(skills) => setForm({ ...form, skills })} required />
          </div>
          <div>
            <label className="label" htmlFor="experience_level">
              Experience level
            </label>
            <select id="experience_level" className="field" value={form.experience_level} onChange={(event) => setForm({ ...form, experience_level: event.target.value })}>
              {experienceLevels.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="preferred_job_type">
              Preferred job type
            </label>
            <select id="preferred_job_type" className="field" value={form.preferred_job_type} onChange={(event) => setForm({ ...form, preferred_job_type: event.target.value })}>
              {jobTypes.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <button className="btn-primary w-full" disabled={saving} type="submit">
              {saving && <Loader2 className="animate-spin" size={18} />}
              Save/update profile
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
