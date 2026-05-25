"use client";

import { FileText, GraduationCap, Loader2, Trash2, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
import SkillMultiSelect from "@/components/SkillMultiSelect";
import { apiFetch, assetUrl } from "@/lib/api";
import { academicStatuses, currentAcademicYears, documentTypes, experienceLevels, graduateLookingFor, internshipPreferences, jobTypes } from "@/lib/options";
import { openProtectedDocument, openProtectedResume } from "@/lib/protectedFiles";
import { splitSkills } from "@/lib/utils";
import { uploadRules, validateUploadFile } from "@/lib/uploadValidation";
import { useAuth } from "@/hooks/useAuth";
import type { JobSeekerDocument, JobSeekerDocumentType, JobSeekerProfile } from "@/types";

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
  preferred_job_type: "Full-time",
  academic_status: "UNDERGRADUATE",
  degree_name: "",
  stream_or_branch: "",
  college_or_university: "",
  admission_year: "",
  expected_graduation_year: "",
  current_year: "3rd Year",
  current_semester: "",
  current_cgpa: "",
  internship_preference: "Internship",
  preferred_internship_duration: "",
  available_from: "",
  open_to_remote: true,
  open_to_relocation: false,
  final_cgpa_or_percentage: "",
  looking_for: "Full-time"
};

const emptyDocumentForm = {
  document_type: "MARKSHEET" as JobSeekerDocumentType,
  title: "",
  related_skill: "",
  issuing_organization: "",
  issue_date: "",
  credential_url: ""
};

export default function JobSeekerProfilePage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [profile, setProfile] = useState<JobSeekerProfile | null>(null);
  const [documents, setDocuments] = useState<JobSeekerDocument[]>([]);
  const [form, setForm] = useState(emptyProfile);
  const [documentForm, setDocumentForm] = useState(emptyDocumentForm);
  const [saving, setSaving] = useState(false);

  const load = () => {
    Promise.all([apiFetch<JobSeekerProfile>("/jobseeker/profile"), apiFetch<JobSeekerDocument[]>("/jobseeker/documents")])
      .then(([data, documentRows]) => {
        setProfile(data);
        setDocuments(documentRows);
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
          preferred_job_type: data.preferred_job_type || "Full-time",
          academic_status: data.academic_status || "UNDERGRADUATE",
          degree_name: data.degree_name || data.degree || "",
          stream_or_branch: data.stream_or_branch || "",
          college_or_university: data.college_or_university || data.college || "",
          admission_year: data.admission_year ? String(data.admission_year) : "",
          expected_graduation_year: data.expected_graduation_year ? String(data.expected_graduation_year) : "",
          current_year: data.current_year || "3rd Year",
          current_semester: data.current_semester || "",
          current_cgpa: data.current_cgpa !== null && data.current_cgpa !== undefined ? String(data.current_cgpa) : "",
          internship_preference: data.internship_preference || "Internship",
          preferred_internship_duration: data.preferred_internship_duration || "",
          available_from: data.available_from || "",
          open_to_remote: data.open_to_remote ?? true,
          open_to_relocation: data.open_to_relocation ?? false,
          final_cgpa_or_percentage: data.final_cgpa_or_percentage || "",
          looking_for: data.looking_for || "Full-time"
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
          degree: form.degree_name || form.degree,
          college: form.college_or_university || form.college,
          passing_year: form.passing_year ? Number(form.passing_year) : form.expected_graduation_year ? Number(form.expected_graduation_year) : null,
          cgpa_or_percentage: form.academic_status === "UNDERGRADUATE" ? form.current_cgpa || null : form.final_cgpa_or_percentage || null,
          admission_year: form.admission_year ? Number(form.admission_year) : null,
          expected_graduation_year: form.expected_graduation_year ? Number(form.expected_graduation_year) : null,
          current_cgpa: form.current_cgpa ? Number(form.current_cgpa) : null,
          available_from: form.available_from || null
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

  const upload = async (file: File | undefined, endpoint: string, rules: (typeof uploadRules)[keyof typeof uploadRules]) => {
    if (!file) return;
    const validationError = validateUploadFile(file, rules);
    if (validationError) {
      toast.error(validationError);
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

  const openResume = async () => {
    if (!profile?.resume_pdf_url) return;
    try {
      await openProtectedResume(profile.resume_pdf_url);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Resume could not be opened");
    }
  };

  const uploadDocument = async (file: File | undefined) => {
    if (!file) return;
    const rules = documentForm.document_type === "RESUME" ? uploadRules.resume : uploadRules.academicDocument;
    const validationError = validateUploadFile(file, rules);
    if (validationError) {
      toast.error(validationError);
      return;
    }
    if (!documentForm.title.trim()) {
      toast.error("Document title is required");
      return;
    }
    const body = new FormData();
    body.append("document_type", documentForm.document_type);
    body.append("title", documentForm.title.trim());
    body.append("related_skill", documentForm.related_skill.trim());
    body.append("issuing_organization", documentForm.issuing_organization.trim());
    body.append("issue_date", documentForm.issue_date);
    body.append("credential_url", documentForm.credential_url.trim());
    body.append("file", file);
    try {
      await apiFetch<JobSeekerDocument>("/jobseeker/documents", { method: "POST", body });
      toast.success("Document uploaded");
      setDocumentForm(emptyDocumentForm);
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Document upload failed");
    }
  };

  const deleteDocument = async (documentId: number) => {
    try {
      await apiFetch(`/jobseeker/documents/${documentId}`, { method: "DELETE" });
      toast.success("Document deleted");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Delete failed");
    }
  };

  const openDocument = async (path: string) => {
    try {
      await openProtectedDocument(path);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Document could not be opened");
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
            <input className="hidden" type="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" onChange={(event) => upload(event.target.files?.[0], "/jobseeker/profile-picture", uploadRules.image)} />
          </label>
          <p className="mt-2 text-xs font-bold text-[#6b767d]">Images: JPG, PNG, WEBP only, max 2 MB.</p>

          <label className="btn-secondary mt-3 w-full cursor-pointer">
            <FileText size={17} />
            Upload resume PDF
            <input className="hidden" type="file" accept="application/pdf,.pdf" onChange={(event) => upload(event.target.files?.[0], "/jobseeker/resume", uploadRules.resume)} />
          </label>
          <p className="mt-2 text-xs font-bold text-[#6b767d]">Resume: PDF only, max 5 MB.</p>
          <p className="mt-3 rounded-lg border border-teal-100 bg-teal-50 p-3 text-xs font-bold leading-6 text-teal-800">
            Your resume is not public. It becomes visible only to recruiters when you apply to their job. Owner/Admin may access it only for moderation or support.
          </p>

          {profile.resume_pdf_url && (
            <button className="mt-4 block w-full rounded-lg bg-teal-50 p-3 text-left text-sm font-black text-teal-700" type="button" onClick={openResume}>
              View uploaded resume
            </button>
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
          <div className="md:col-span-2 rounded-lg border border-black/10 bg-white/70 p-4">
            <div className="mb-4 flex items-center gap-2">
              <GraduationCap size={18} />
              <h2 className="text-lg font-black">Academic Profile</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <Select label="Academic Status" value={form.academic_status} options={academicStatuses} onChange={(value) => setForm({ ...form, academic_status: value })} />
              <Input label="Degree name" name="degree_name" value={form.degree_name} onChange={(value) => setForm({ ...form, degree_name: value })} />
              <Input label="Stream or branch" name="stream_or_branch" value={form.stream_or_branch} onChange={(value) => setForm({ ...form, stream_or_branch: value })} />
              <Input label="College or university" name="college_or_university" value={form.college_or_university} onChange={(value) => setForm({ ...form, college_or_university: value })} />
              {form.academic_status === "UNDERGRADUATE" ? (
                <>
                  <Input label="Admission/joining year" name="admission_year" value={form.admission_year} onChange={(value) => setForm({ ...form, admission_year: value })} type="number" />
                  <Input label="Expected graduation year" name="expected_graduation_year" value={form.expected_graduation_year} onChange={(value) => setForm({ ...form, expected_graduation_year: value })} type="number" />
                  <Select label="Current year" value={form.current_year} options={currentAcademicYears} onChange={(value) => setForm({ ...form, current_year: value })} />
                  <Input label="Current semester" name="current_semester" value={form.current_semester} onChange={(value) => setForm({ ...form, current_semester: value })} />
                  <Input label="Current CGPA" name="current_cgpa" value={form.current_cgpa} onChange={(value) => setForm({ ...form, current_cgpa: value })} type="number" />
                  <Select label="Internship preference" value={form.internship_preference} options={internshipPreferences} onChange={(value) => setForm({ ...form, internship_preference: value })} />
                  <Input label="Preferred internship duration" name="preferred_internship_duration" value={form.preferred_internship_duration} onChange={(value) => setForm({ ...form, preferred_internship_duration: value })} />
                  <Input label="Available from" name="available_from" value={form.available_from} onChange={(value) => setForm({ ...form, available_from: value })} type="date" />
                </>
              ) : (
                <>
                  <Input label="Passing year" name="graduate_passing_year" value={form.passing_year} onChange={(value) => setForm({ ...form, passing_year: value })} type="number" />
                  <Input label="Final CGPA/percentage" name="final_cgpa_or_percentage" value={form.final_cgpa_or_percentage} onChange={(value) => setForm({ ...form, final_cgpa_or_percentage: value })} />
                  <Select label="Graduate experience level" value={form.experience_level} options={experienceLevels} onChange={(value) => setForm({ ...form, experience_level: value })} />
                  <Select label="Looking for" value={form.looking_for} options={graduateLookingFor} onChange={(value) => setForm({ ...form, looking_for: value })} />
                </>
              )}
              <label className="flex items-center gap-3 rounded-lg border border-black/10 bg-white p-3 text-sm font-black text-[#526069]">
                <input type="checkbox" checked={form.open_to_remote} onChange={(event) => setForm({ ...form, open_to_remote: event.target.checked })} />
                Open to remote
              </label>
              <label className="flex items-center gap-3 rounded-lg border border-black/10 bg-white p-3 text-sm font-black text-[#526069]">
                <input type="checkbox" checked={form.open_to_relocation} onChange={(event) => setForm({ ...form, open_to_relocation: event.target.checked })} />
                Open to relocation
              </label>
            </div>
          </div>
          <div className="md:col-span-2">
            <button className="btn-primary w-full" disabled={saving} type="submit">
              {saving && <Loader2 className="animate-spin" size={18} />}
              Save/update profile
            </button>
          </div>
        </form>
      </div>
      <section className="panel mt-5 p-5">
        <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
          <div>
            <h2 className="text-xl font-black">Documents and Certificates</h2>
            <p className="mt-1 text-sm font-bold text-[#6b767d]">Resume: PDF only, max 5 MB. Academic documents: PDF, JPG, PNG, WEBP, max 5 MB.</p>
          </div>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <Select label="Document type" value={documentForm.document_type} options={documentTypes} onChange={(value) => setDocumentForm({ ...documentForm, document_type: value as JobSeekerDocumentType })} />
          <Input label="Document title" name="document_title" value={documentForm.title} onChange={(value) => setDocumentForm({ ...documentForm, title: value })} />
          <Input label="Related skill" name="related_skill" value={documentForm.related_skill} onChange={(value) => setDocumentForm({ ...documentForm, related_skill: value })} />
          <Input label="Issuing organization" name="issuing_organization" value={documentForm.issuing_organization} onChange={(value) => setDocumentForm({ ...documentForm, issuing_organization: value })} />
          <Input label="Issue date" name="issue_date" value={documentForm.issue_date} onChange={(value) => setDocumentForm({ ...documentForm, issue_date: value })} type="date" />
          <Input label="Credential URL" name="credential_url" value={documentForm.credential_url} onChange={(value) => setDocumentForm({ ...documentForm, credential_url: value })} />
        </div>
        <label className="btn-secondary mt-4 inline-flex cursor-pointer">
          <Upload size={17} />
          Upload document
          <input
            className="hidden"
            type="file"
            accept={documentForm.document_type === "RESUME" ? "application/pdf,.pdf" : "application/pdf,image/jpeg,image/png,image/webp,.pdf,.jpg,.jpeg,.png,.webp"}
            onChange={(event) => uploadDocument(event.target.files?.[0])}
          />
        </label>

        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {documents.length === 0 ? (
            <p className="text-sm font-bold text-[#6b767d]">No documents uploaded yet.</p>
          ) : (
            documents.map((document) => (
              <article key={document.id} className="rounded-lg border border-black/10 bg-white/70 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-black text-teal-700">{document.document_type.replaceAll("_", " ")}</p>
                    <h3 className="mt-1 font-black">{document.title}</h3>
                    <p className="mt-1 text-xs font-bold text-[#6b767d]">{document.original_filename}</p>
                  </div>
                  <button className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-rose-700" type="button" onClick={() => deleteDocument(document.id)} title="Delete document">
                    <Trash2 size={16} />
                  </button>
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs font-black text-[#526069]">
                  {document.related_skill && <span className="rounded-full bg-teal-50 px-3 py-1 text-teal-700">{document.related_skill}</span>}
                  {document.issuing_organization && <span className="rounded-full bg-amber-50 px-3 py-1 text-amber-700">{document.issuing_organization}</span>}
                  {document.is_verified && <span className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-700">Verified</span>}
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button className="btn-secondary !py-2" type="button" onClick={() => openDocument(document.file_url)}>
                    <FileText size={16} />
                    View
                  </button>
                  {document.credential_url && (
                    <a className="btn-secondary !py-2" href={document.credential_url} target="_blank" rel="noreferrer">
                      Credential
                    </a>
                  )}
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </main>
  );
}

function Input({ label, name, value, onChange, required, type = "text", disabled = false }: { label: string; name: string; value: string; onChange: (value: string) => void; required?: boolean; type?: string; disabled?: boolean }) {
  return (
    <div>
      <label className="label" htmlFor={name}>
        {label}
      </label>
      <input id={name} className="field disabled:bg-stone-100" required={required} type={type} value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} />
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
