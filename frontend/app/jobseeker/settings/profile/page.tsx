"use client";

import { FileText, Loader2, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
import SkillMultiSelect from "@/components/SkillMultiSelect";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl } from "@/lib/api";
import { experienceLevels, jobTypes } from "@/lib/options";
import { splitSkills } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { JobSeekerProfile, PublicProfile, UserDocument } from "@/types";

const emptyProfile = {
  phone: "",
  github_url: "",
  about: "",
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

export default function JobSeekerProfileSettingsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [profile, setProfile] = useState<JobSeekerProfile | null>(null);
  const [publicProfile, setPublicProfile] = useState<PublicProfile | null>(null);
  const [documents, setDocuments] = useState<UserDocument[]>([]);
  const [form, setForm] = useState(emptyProfile);
  const [username, setUsername] = useState("");
  const [visibility, setVisibility] = useState<"PUBLIC" | "PRIVATE">("PUBLIC");
  const [saving, setSaving] = useState(false);
  const [documentType, setDocumentType] = useState("certificate");
  const [documentPublic, setDocumentPublic] = useState(false);

  const load = () => {
    Promise.all([
      apiFetch<JobSeekerProfile>("/jobseeker/profile"),
      apiFetch<PublicProfile>("/profiles/me"),
      apiFetch<UserDocument[]>("/profiles/me/documents")
    ])
      .then(([profileData, publicData, documentRows]) => {
        setProfile(profileData);
        setPublicProfile(publicData);
        setDocuments(documentRows);
        setUsername(publicData.username || "");
        setVisibility(publicData.profile_visibility);
        setForm({
          phone: profileData.phone || "",
          github_url: profileData.github_url || "",
          about: profileData.about || publicData.bio || "",
          education: profileData.education || "",
          degree: profileData.degree || "",
          college: profileData.college || "",
          passing_year: profileData.passing_year ? String(profileData.passing_year) : "",
          cgpa_or_percentage: profileData.cgpa_or_percentage || "",
          skills: profileData.skills_list?.length ? profileData.skills_list : splitSkills(profileData.skills),
          experience_level: profileData.experience_level || "Fresher",
          preferred_location: profileData.preferred_location || "",
          preferred_job_type: profileData.preferred_job_type || "Full-time"
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
      if (username.trim() && username.trim() !== publicProfile?.username) {
        await apiFetch<PublicProfile>("/profiles/me/username", {
          method: "PUT",
          body: JSON.stringify({ username: username.trim() })
        });
      }
      await apiFetch<PublicProfile>("/profiles/me/settings", {
        method: "PUT",
        body: JSON.stringify({ bio: form.about, profile_visibility: visibility })
      });
      setProfile(updated);
      toast.success("Profile settings saved");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const upload = async (file: File | undefined, endpoint: string, maxBytes: number, pdfOnly = false) => {
    if (!file) return;
    if (file.size > maxBytes) return toast.error("File size is too large");
    if (pdfOnly && file.type !== "application/pdf") return toast.error("Resume must be a PDF");
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

  const uploadDocument = async (file: File | undefined) => {
    if (!file) return;
    const body = new FormData();
    body.append("document_type", documentType);
    body.append("is_public", String(documentPublic));
    body.append("file", file);
    try {
      await apiFetch<UserDocument>("/profiles/me/documents", { method: "POST", body });
      toast.success("Document uploaded for verification");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Document upload failed");
    }
  };

  if (loading || !profile) return <main className="page-shell">Loading profile settings...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Profile Settings" eyebrow="Job seeker" />
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
            <p className="text-sm font-bold text-[#6b767d]">ID {profile.public_user_id || publicProfile?.public_user_id}</p>
            <div className="mt-2"><VerificationStatusBadge status={profile.verification_status || "PENDING"} /></div>
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
            Private documents are never shown publicly. Public profile documents list titles only.
          </p>
        </aside>

        <div className="grid gap-5">
          <form onSubmit={submit} className="panel grid gap-4 p-5 md:grid-cols-2">
            <div>
              <label className="label" htmlFor="username">Username</label>
              <input id="username" className="field" value={username} onChange={(event) => setUsername(event.target.value.toLowerCase())} />
            </div>
            <div>
              <label className="label" htmlFor="visibility">Profile visibility</label>
              <select id="visibility" className="field" value={visibility} onChange={(event) => setVisibility(event.target.value as "PUBLIC" | "PRIVATE")}>
                <option value="PUBLIC">Public</option>
                <option value="PRIVATE">Private</option>
              </select>
            </div>
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
                <label className="label" htmlFor={key}>{label}</label>
                <input id={key} className="field" value={form[key as keyof typeof form] as string} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />
              </div>
            ))}
            <div className="md:col-span-2">
              <label className="label" htmlFor="about">About</label>
              <textarea id="about" className="field min-h-28" value={form.about} onChange={(event) => setForm({ ...form, about: event.target.value })} />
            </div>
            <div className="md:col-span-2">
              <SkillMultiSelect label="Skills" selected={form.skills} onChange={(skills) => setForm({ ...form, skills })} required />
            </div>
            <div>
              <label className="label" htmlFor="experience_level">Experience level</label>
              <select id="experience_level" className="field" value={form.experience_level} onChange={(event) => setForm({ ...form, experience_level: event.target.value })}>
                {experienceLevels.map((item) => <option key={item}>{item}</option>)}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="preferred_job_type">Preferred job type</label>
              <select id="preferred_job_type" className="field" value={form.preferred_job_type} onChange={(event) => setForm({ ...form, preferred_job_type: event.target.value })}>
                {jobTypes.map((item) => <option key={item}>{item}</option>)}
              </select>
            </div>
            <div className="md:col-span-2">
              <button className="btn-primary w-full" disabled={saving} type="submit">
                {saving && <Loader2 className="animate-spin" size={18} />}
                Save settings
              </button>
            </div>
          </form>

          <section className="panel p-5">
            <h2 className="text-xl font-black">Verification Documents</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
              <select className="field" value={documentType} onChange={(event) => setDocumentType(event.target.value)}>
                {["certificate", "marksheet_10", "marksheet_12", "diploma", "graduation", "post_graduation", "resume"].map((item) => (
                  <option key={item} value={item}>{item.replaceAll("_", " ")}</option>
                ))}
              </select>
              <label className="flex items-center gap-2 text-sm font-bold text-[#526069]">
                <input type="checkbox" checked={documentPublic} onChange={(event) => setDocumentPublic(event.target.checked)} />
                Show title publicly
              </label>
              <label className="btn-secondary cursor-pointer">
                Upload
                <input className="hidden" type="file" accept="application/pdf,image/png,image/jpeg,image/webp" onChange={(event) => uploadDocument(event.target.files?.[0])} />
              </label>
            </div>
            <div className="mt-4 grid gap-2">
              {documents.map((document) => (
                <div key={document.id} className="rounded-lg bg-white/70 p-3 text-sm font-bold text-[#526069]">
                  {document.document_type.replaceAll("_", " ")} / {document.verification_status} / {document.is_public ? "public title" : "private"}
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
