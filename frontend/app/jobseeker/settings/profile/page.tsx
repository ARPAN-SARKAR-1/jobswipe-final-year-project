"use client";

import { FileText, Loader2, Trash2, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
import SkillMultiSelect from "@/components/SkillMultiSelect";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl } from "@/lib/api";
import { fileGuidance, ruleForDocumentType, uploadRules, validateFile, type FileValidationRule } from "@/lib/fileValidation";
import { experienceLevels, jobTypes } from "@/lib/options";
import { splitSkills } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type {
  JobSeekerCategory,
  JobSeekerProfile,
  JobSeekerRecommendation,
  JobSeekerReference,
  PublicProfile,
  SectionVisibility,
  UserDocument
} from "@/types";

type ProfileForm = {
  phone: string;
  github_url: string;
  about: string;
  education: string;
  degree: string;
  college: string;
  passing_year: string;
  cgpa_or_percentage: string;
  skills: string[];
  experience_level: string;
  preferred_location: string;
  preferred_job_type: string;
  job_seeker_category: JobSeekerCategory | "";
  college_name: string;
  university_name: string;
  course_name: string;
  degree_name: string;
  department_or_branch: string;
  current_year_or_semester: string;
  expected_passing_year: string;
  college_location: string;
  student_id_number: string;
  internship_interest: boolean;
  preferred_internship_roles: string;
  highest_degree: string;
  graduation_year: string;
  specialization_or_branch: string;
  fresher_skills: string;
  certifications: string;
  project_links: string;
  internship_experience: string;
  preferred_job_roles: string;
  total_experience_years: string;
  current_or_last_company: string;
  current_or_last_role: string;
  employment_type: string;
  notice_period: string;
  previous_companies: string;
  role_history: string;
  key_responsibilities: string;
  tools_technologies: string;
  achievements: string;
  preferred_next_roles: string;
  education_visibility: SectionVisibility;
  experience_visibility: SectionVisibility;
  recommendation_visibility: SectionVisibility;
  reference_visibility: SectionVisibility;
  certificate_visibility: SectionVisibility;
};

const emptyProfile: ProfileForm = {
  phone: "",
  github_url: "",
  about: "",
  education: "",
  degree: "",
  college: "",
  passing_year: "",
  cgpa_or_percentage: "",
  skills: [],
  experience_level: "Fresher",
  preferred_location: "",
  preferred_job_type: "Full-time",
  job_seeker_category: "",
  college_name: "",
  university_name: "",
  course_name: "",
  degree_name: "",
  department_or_branch: "",
  current_year_or_semester: "",
  expected_passing_year: "",
  college_location: "",
  student_id_number: "",
  internship_interest: false,
  preferred_internship_roles: "",
  highest_degree: "",
  graduation_year: "",
  specialization_or_branch: "",
  fresher_skills: "",
  certifications: "",
  project_links: "",
  internship_experience: "",
  preferred_job_roles: "",
  total_experience_years: "",
  current_or_last_company: "",
  current_or_last_role: "",
  employment_type: "",
  notice_period: "",
  previous_companies: "",
  role_history: "",
  key_responsibilities: "",
  tools_technologies: "",
  achievements: "",
  preferred_next_roles: "",
  education_visibility: "PUBLIC",
  experience_visibility: "PUBLIC",
  recommendation_visibility: "PRIVATE",
  reference_visibility: "PRIVATE",
  certificate_visibility: "PUBLIC"
};

const categoryOptions: { label: string; value: JobSeekerCategory }[] = [
  { label: "Undergraduate student", value: "UNDERGRADUATE" },
  { label: "Graduate fresher", value: "GRADUATE_FRESHER" },
  { label: "Graduate experienced", value: "GRADUATE_EXPERIENCED" }
];

const documentTypes = [
  "certificate",
  "college_id_card",
  "library_card",
  "bonafide_certificate",
  "admission_proof",
  "fee_receipt",
  "graduation_marksheet",
  "degree_certificate",
  "provisional_certificate",
  "experience_letter",
  "relieving_letter",
  "offer_letter",
  "salary_slip",
  "recommendation_letter",
  "reference_letter",
  "marksheet_10",
  "marksheet_12",
  "diploma",
  "graduation",
  "post_graduation",
  "resume",
  "other"
];

const privateOnlyDocumentTypes = new Set([
  "resume",
  "marksheet_10",
  "marksheet_12",
  "diploma",
  "graduation",
  "post_graduation",
  "college_id_card",
  "library_card",
  "bonafide_certificate",
  "admission_proof",
  "fee_receipt",
  "graduation_marksheet",
  "degree_certificate",
  "provisional_certificate",
  "experience_letter",
  "relieving_letter",
  "offer_letter",
  "salary_slip",
  "reference_letter"
]);

const visibilityOptions: { label: string; value: SectionVisibility }[] = [
  { label: "Private", value: "PRIVATE" },
  { label: "Recruiters only", value: "RECRUITERS_ONLY" },
  { label: "Public", value: "PUBLIC" }
];

function toForm(profileData: JobSeekerProfile, publicData: PublicProfile): ProfileForm {
  return {
    ...emptyProfile,
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
    preferred_job_type: profileData.preferred_job_type || "Full-time",
    job_seeker_category: profileData.job_seeker_category || "",
    college_name: profileData.college_name || "",
    university_name: profileData.university_name || "",
    course_name: profileData.course_name || "",
    degree_name: profileData.degree_name || "",
    department_or_branch: profileData.department_or_branch || "",
    current_year_or_semester: profileData.current_year_or_semester || "",
    expected_passing_year: profileData.expected_passing_year ? String(profileData.expected_passing_year) : "",
    college_location: profileData.college_location || "",
    student_id_number: profileData.student_id_number || "",
    internship_interest: Boolean(profileData.internship_interest),
    preferred_internship_roles: profileData.preferred_internship_roles || "",
    highest_degree: profileData.highest_degree || "",
    graduation_year: profileData.graduation_year ? String(profileData.graduation_year) : "",
    specialization_or_branch: profileData.specialization_or_branch || "",
    fresher_skills: profileData.fresher_skills || "",
    certifications: profileData.certifications || "",
    project_links: profileData.project_links || "",
    internship_experience: profileData.internship_experience || "",
    preferred_job_roles: profileData.preferred_job_roles || "",
    total_experience_years: profileData.total_experience_years != null ? String(profileData.total_experience_years) : "",
    current_or_last_company: profileData.current_or_last_company || "",
    current_or_last_role: profileData.current_or_last_role || "",
    employment_type: profileData.employment_type || "",
    notice_period: profileData.notice_period || "",
    previous_companies: profileData.previous_companies || "",
    role_history: profileData.role_history || "",
    key_responsibilities: profileData.key_responsibilities || "",
    tools_technologies: profileData.tools_technologies || "",
    achievements: profileData.achievements || "",
    preferred_next_roles: profileData.preferred_next_roles || "",
    education_visibility: profileData.education_visibility || "PUBLIC",
    experience_visibility: profileData.experience_visibility || "PUBLIC",
    recommendation_visibility: profileData.recommendation_visibility || "PRIVATE",
    reference_visibility: profileData.reference_visibility || "PRIVATE",
    certificate_visibility: profileData.certificate_visibility || "PUBLIC"
  };
}

function numberOrNull(value: string) {
  return value.trim() ? Number(value) : null;
}

function fieldLabel(value: string) {
  return value.replaceAll("_", " ").toLowerCase();
}

export default function JobSeekerProfileSettingsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [profile, setProfile] = useState<JobSeekerProfile | null>(null);
  const [publicProfile, setPublicProfile] = useState<PublicProfile | null>(null);
  const [documents, setDocuments] = useState<UserDocument[]>([]);
  const [recommendations, setRecommendations] = useState<JobSeekerRecommendation[]>([]);
  const [references, setReferences] = useState<JobSeekerReference[]>([]);
  const [form, setForm] = useState<ProfileForm>(emptyProfile);
  const [username, setUsername] = useState("");
  const [visibility, setVisibility] = useState<"PUBLIC" | "PRIVATE">("PUBLIC");
  const [saving, setSaving] = useState(false);
  const [documentType, setDocumentType] = useState("certificate");
  const [documentVisibility, setDocumentVisibility] = useState<SectionVisibility>("PRIVATE");
  const [recommendationForm, setRecommendationForm] = useState({
    title: "",
    organization: "",
    issued_by: "",
    issue_date: "",
    visibility: "PRIVATE" as SectionVisibility
  });
  const [referenceForm, setReferenceForm] = useState({
    reference_name: "",
    reference_role: "",
    organization: "",
    relationship: "",
    email: "",
    phone: "",
    visibility: "PRIVATE" as "PRIVATE" | "RECRUITERS_ONLY",
    note: ""
  });

  const load = () => {
    Promise.all([
      apiFetch<JobSeekerProfile>("/jobseeker/profile"),
      apiFetch<PublicProfile>("/profiles/me"),
      apiFetch<UserDocument[]>("/jobseeker/documents"),
      apiFetch<JobSeekerRecommendation[]>("/jobseeker/recommendations"),
      apiFetch<JobSeekerReference[]>("/jobseeker/references")
    ])
      .then(([profileData, publicData, documentRows, recommendationRows, referenceRows]) => {
        setProfile(profileData);
        setPublicProfile(publicData);
        setDocuments(documentRows);
        setRecommendations(recommendationRows);
        setReferences(referenceRows);
        setUsername(publicData.username || "");
        setVisibility(publicData.profile_visibility);
        setForm(toForm(profileData, publicData));
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
      const payload = {
        ...form,
        job_seeker_category: form.job_seeker_category || null,
        passing_year: numberOrNull(form.passing_year),
        expected_passing_year: numberOrNull(form.expected_passing_year),
        graduation_year: numberOrNull(form.graduation_year),
        total_experience_years: numberOrNull(form.total_experience_years)
      };
      const updated = await apiFetch<JobSeekerProfile>("/jobseeker/profile", {
        method: "PUT",
        body: JSON.stringify(payload)
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

  const upload = async (file: File | undefined, endpoint: string, rule: FileValidationRule) => {
    if (!file) return;
    const validationError = validateFile(file, rule);
    if (validationError) return toast.error(validationError);
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
    const rule = ruleForDocumentType(documentType);
    const validationError = validateFile(file, rule);
    if (validationError) return toast.error(validationError);
    const body = new FormData();
    body.append("document_type", documentType);
    body.append("visibility", documentVisibility);
    body.append("file", file);
    try {
      await apiFetch<UserDocument>("/jobseeker/documents", { method: "POST", body });
      toast.success("Document uploaded for verification");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Document upload failed");
    }
  };

  const updateDocumentVisibility = async (document: UserDocument, nextVisibility: SectionVisibility) => {
    try {
      await apiFetch<UserDocument>(`/jobseeker/documents/${document.id}/visibility`, {
        method: "PATCH",
        body: JSON.stringify({ visibility: nextVisibility })
      });
      toast.success("Document visibility updated");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Visibility update failed");
    }
  };

  const deleteDocument = async (document: UserDocument) => {
    try {
      await apiFetch(`/jobseeker/documents/${document.id}`, { method: "DELETE" });
      toast.success("Document removed");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Delete failed");
    }
  };

  const createRecommendation = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await apiFetch<JobSeekerRecommendation>("/jobseeker/recommendations", {
        method: "POST",
        body: JSON.stringify({
          ...recommendationForm,
          issue_date: recommendationForm.issue_date || null
        })
      });
      setRecommendationForm({ title: "", organization: "", issued_by: "", issue_date: "", visibility: "PRIVATE" });
      toast.success("Recommendation saved");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Recommendation failed");
    }
  };

  const createReference = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await apiFetch<JobSeekerReference>("/jobseeker/references", {
        method: "POST",
        body: JSON.stringify(referenceForm)
      });
      setReferenceForm({ reference_name: "", reference_role: "", organization: "", relationship: "", email: "", phone: "", visibility: "PRIVATE", note: "" });
      toast.success("Reference saved privately");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Reference failed");
    }
  };

  const deleteRecommendation = async (recommendation: JobSeekerRecommendation) => {
    try {
      await apiFetch(`/jobseeker/recommendations/${recommendation.id}`, { method: "DELETE" });
      toast.success("Recommendation removed");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Delete failed");
    }
  };

  const deleteReference = async (reference: JobSeekerReference) => {
    try {
      await apiFetch(`/jobseeker/references/${reference.id}`, { method: "DELETE" });
      toast.success("Reference removed");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Delete failed");
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
            <div className="mt-2 flex flex-wrap justify-center gap-2">
              <VerificationStatusBadge status={profile.verification_status || "PENDING"} />
              <VerificationStatusBadge status={profile.student_verification_status || "STUDENT_UNVERIFIED"} />
              <VerificationStatusBadge status={profile.graduation_verification_status || "GRADUATION_UNVERIFIED"} />
              <VerificationStatusBadge status={profile.experience_verification_status || "EXPERIENCE_UNVERIFIED"} />
            </div>
          </div>
          <div className="mt-5 rounded-lg bg-[#fbfaf7] p-3">
            <p className="text-sm font-black text-[#172026]">Profile completion: {profile.profile_completion_percentage || 0}%</p>
            <div className="mt-2 h-2 rounded-lg bg-stone-200">
              <div className="h-2 rounded-lg bg-teal-600" style={{ width: `${profile.profile_completion_percentage || 0}%` }} />
            </div>
            {profile.missing_profile_fields && profile.missing_profile_fields.length > 0 && (
              <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs font-bold leading-5 text-amber-800">
                <p className="font-black">Missing to apply:</p>
                <ul className="mt-1 list-inside list-disc">
                  {profile.missing_profile_fields.slice(0, 8).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <label className="btn-secondary mt-5 w-full cursor-pointer">
            Upload picture
            <input
              className="hidden"
              type="file"
              accept={uploadRules.profilePhoto.accept}
              onChange={(event) => {
                void upload(event.target.files?.[0], "/jobseeker/profile-picture", uploadRules.profilePhoto);
                event.currentTarget.value = "";
              }}
            />
          </label>
          <p className="mt-2 text-xs font-bold text-[#8a949a]">{fileGuidance(uploadRules.profilePhoto)}</p>

          <label className="btn-secondary mt-3 w-full cursor-pointer">
            <FileText size={17} />
            Upload resume
            <input
              className="hidden"
              type="file"
              accept={uploadRules.resume.accept}
              onChange={(event) => {
                void upload(event.target.files?.[0], "/jobseeker/resume", uploadRules.resume);
                event.currentTarget.value = "";
              }}
            />
          </label>
          <p className="mt-2 text-xs font-bold text-[#8a949a]">{fileGuidance(uploadRules.resume)}</p>
          <p className="mt-3 rounded-lg border border-teal-100 bg-teal-50 p-3 text-xs font-bold leading-6 text-teal-800">
            Student ID documents are private and used only for verification. Public profile documents list titles only.
          </p>
        </aside>

        <div className="grid gap-5">
          <form onSubmit={submit} className="grid gap-5">
            <section className="panel grid gap-4 p-5 md:grid-cols-2">
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
              <div className="md:col-span-2">
                <label className="label" htmlFor="job_seeker_category">Job seeker category</label>
                <select id="job_seeker_category" className="field" value={form.job_seeker_category} onChange={(event) => setForm({ ...form, job_seeker_category: event.target.value as JobSeekerCategory })}>
                  <option value="">Select category</option>
                  {categoryOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </div>
              <div>
                <label className="label" htmlFor="phone">Phone number</label>
                <input id="phone" className="field" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
              </div>
              <div>
                <label className="label" htmlFor="github_url">Portfolio/GitHub/LinkedIn</label>
                <input id="github_url" className="field" value={form.github_url} onChange={(event) => setForm({ ...form, github_url: event.target.value })} />
              </div>
              <div className="md:col-span-2">
                <label className="label" htmlFor="about">About</label>
                <textarea id="about" className="field min-h-28" value={form.about} onChange={(event) => setForm({ ...form, about: event.target.value })} />
              </div>
              <div className="md:col-span-2">
                <SkillMultiSelect label="Skills" selected={form.skills} onChange={(skills) => setForm({ ...form, skills })} required />
              </div>
            </section>

            <section className="panel grid gap-4 p-5 md:grid-cols-2">
              <div className="md:col-span-2 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-black">Education and Category Details</h2>
                <select className="field max-w-xs" value={form.education_visibility} onChange={(event) => setForm({ ...form, education_visibility: event.target.value as SectionVisibility })}>
                  {visibilityOptions.map((item) => <option key={item.value} value={item.value}>Education: {item.label}</option>)}
                </select>
              </div>
              {[
                ["Education", "education"],
                ["Degree", "degree"],
                ["College/university", "college"],
                ["Passing year", "passing_year"],
                ["CGPA/percentage", "cgpa_or_percentage"],
                ["Preferred location", "preferred_location"]
              ].map(([label, key]) => (
                <div key={key}>
                  <label className="label" htmlFor={key}>{label}</label>
                  <input id={key} className="field" value={form[key as keyof ProfileForm] as string} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />
                </div>
              ))}
              {form.job_seeker_category === "UNDERGRADUATE" && (
                <>
                  {[
                    ["College name", "college_name"],
                    ["University name", "university_name"],
                    ["Course name", "course_name"],
                    ["Degree name", "degree_name"],
                    ["Department or branch", "department_or_branch"],
                    ["Current year or semester", "current_year_or_semester"],
                    ["Expected passing year", "expected_passing_year"],
                    ["College location", "college_location"],
                    ["Student ID number (private)", "student_id_number"],
                    ["Preferred internship roles", "preferred_internship_roles"]
                  ].map(([label, key]) => (
                    <div key={key}>
                      <label className="label" htmlFor={key}>{label}</label>
                      <input id={key} className="field" value={form[key as keyof ProfileForm] as string} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />
                    </div>
                  ))}
                  <label className="flex items-center gap-2 text-sm font-bold text-[#526069]">
                    <input type="checkbox" checked={form.internship_interest} onChange={(event) => setForm({ ...form, internship_interest: event.target.checked })} />
                    Interested in internships
                  </label>
                </>
              )}
              {form.job_seeker_category === "GRADUATE_FRESHER" && (
                <>
                  {[
                    ["Highest degree", "highest_degree"],
                    ["Graduation year", "graduation_year"],
                    ["Specialization or branch", "specialization_or_branch"],
                    ["Fresher skills", "fresher_skills"],
                    ["Certifications", "certifications"],
                    ["Project links", "project_links"],
                    ["Internship experience", "internship_experience"],
                    ["Preferred job roles", "preferred_job_roles"]
                  ].map(([label, key]) => (
                    <div key={key} className={key.includes("links") || key.includes("experience") || key.includes("roles") ? "md:col-span-2" : ""}>
                      <label className="label" htmlFor={key}>{label}</label>
                      <textarea id={key} className="field min-h-20" value={form[key as keyof ProfileForm] as string} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />
                    </div>
                  ))}
                </>
              )}
            </section>

            <section className="panel grid gap-4 p-5 md:grid-cols-2">
              <div className="md:col-span-2 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-black">Experience</h2>
                <select className="field max-w-xs" value={form.experience_visibility} onChange={(event) => setForm({ ...form, experience_visibility: event.target.value as SectionVisibility })}>
                  {visibilityOptions.map((item) => <option key={item.value} value={item.value}>Experience: {item.label}</option>)}
                </select>
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
              {form.job_seeker_category === "GRADUATE_EXPERIENCED" && (
                <>
                  {[
                    ["Total experience years", "total_experience_years"],
                    ["Current or last company", "current_or_last_company"],
                    ["Current or last role", "current_or_last_role"],
                    ["Employment type", "employment_type"],
                    ["Notice period", "notice_period"],
                    ["Previous companies", "previous_companies"],
                    ["Role history", "role_history"],
                    ["Key responsibilities", "key_responsibilities"],
                    ["Tools and technologies", "tools_technologies"],
                    ["Achievements", "achievements"],
                    ["Preferred next roles", "preferred_next_roles"]
                  ].map(([label, key]) => (
                    <div key={key} className={["previous_companies", "role_history", "key_responsibilities", "tools_technologies", "achievements", "preferred_next_roles"].includes(key) ? "md:col-span-2" : ""}>
                      <label className="label" htmlFor={key}>{label}</label>
                      <textarea id={key} className="field min-h-20" value={form[key as keyof ProfileForm] as string} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />
                    </div>
                  ))}
                </>
              )}
              <div className="md:col-span-2">
                <button className="btn-primary w-full" disabled={saving} type="submit">
                  {saving && <Loader2 className="animate-spin" size={18} />}
                  Save settings
                </button>
              </div>
            </section>
          </form>

          <section className="panel p-5">
            <h2 className="text-xl font-black">Verification Documents</h2>
            <p className="mt-2 text-sm font-bold leading-6 text-[#6b767d]">
              Upload college proof, graduation proof, experience documents, certificates, or recommendation letters. Private proof files are visible only to authorized reviewers.
            </p>
            <div className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
              <select className="field" value={documentType} onChange={(event) => setDocumentType(event.target.value)}>
                {documentTypes.map((item) => (
                  <option key={item} value={item}>{fieldLabel(item)}</option>
                ))}
              </select>
              <select className="field" value={documentVisibility} onChange={(event) => setDocumentVisibility(event.target.value as SectionVisibility)} disabled={privateOnlyDocumentTypes.has(documentType)}>
                {visibilityOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
              <label className="btn-secondary cursor-pointer">
                Upload
                <input
                  className="hidden"
                  type="file"
                  accept={ruleForDocumentType(documentType).accept}
                  onChange={(event) => {
                    void uploadDocument(event.target.files?.[0]);
                    event.currentTarget.value = "";
                  }}
                />
              </label>
            </div>
            <p className="mt-2 text-xs font-bold text-[#8a949a]">{fileGuidance(ruleForDocumentType(documentType))}</p>
            {privateOnlyDocumentTypes.has(documentType) && (
              <p className="mt-2 text-xs font-bold text-[#8a949a]">This document type is forced private for safety.</p>
            )}
            <div className="mt-4 grid gap-2">
              {documents.length === 0 && <p className="rounded-lg bg-white/70 p-3 text-sm font-bold text-[#6b767d]">No verification documents uploaded yet.</p>}
              {documents.map((document) => (
                <div key={document.id} className="grid gap-3 rounded-lg bg-white/70 p-3 text-sm font-bold text-[#526069] md:grid-cols-[1fr_auto_auto] md:items-center">
                  <div>
                    <p className="font-black text-[#172026]">{fieldLabel(document.document_type)}</p>
                    <p>{document.original_filename || "Private verification document"} / {document.verification_status}</p>
                  </div>
                  <select
                    className="field"
                    value={document.visibility}
                    disabled={privateOnlyDocumentTypes.has(document.document_type)}
                    onChange={(event) => updateDocumentVisibility(document, event.target.value as SectionVisibility)}
                  >
                    {visibilityOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                  <button className="btn-secondary !px-3 !py-2 text-rose-700" type="button" onClick={() => deleteDocument(document)}>
                    <Trash2 size={16} />
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section className="panel p-5">
            <h2 className="text-xl font-black">Recommendations</h2>
            <form onSubmit={createRecommendation} className="mt-4 grid gap-3 md:grid-cols-2">
              <input className="field" placeholder="Title" value={recommendationForm.title} onChange={(event) => setRecommendationForm({ ...recommendationForm, title: event.target.value })} required />
              <input className="field" placeholder="Organization/company/college" value={recommendationForm.organization} onChange={(event) => setRecommendationForm({ ...recommendationForm, organization: event.target.value })} />
              <input className="field" placeholder="Issued by" value={recommendationForm.issued_by} onChange={(event) => setRecommendationForm({ ...recommendationForm, issued_by: event.target.value })} />
              <input className="field" type="date" value={recommendationForm.issue_date} onChange={(event) => setRecommendationForm({ ...recommendationForm, issue_date: event.target.value })} />
              <select className="field" value={recommendationForm.visibility} onChange={(event) => setRecommendationForm({ ...recommendationForm, visibility: event.target.value as SectionVisibility })}>
                {visibilityOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
              <button className="btn-primary" type="submit">Add recommendation</button>
            </form>
            <div className="mt-4 grid gap-2">
              {recommendations.map((item) => (
                <div key={item.id} className="flex flex-col gap-3 rounded-lg bg-white/70 p-3 text-sm font-bold text-[#526069] sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-black text-[#172026]">{item.title}</p>
                    <p>{[item.organization, item.issued_by, item.visibility].filter(Boolean).join(" / ")}</p>
                  </div>
                  <button className="btn-secondary !px-3 !py-2 text-rose-700" type="button" onClick={() => deleteRecommendation(item)}>
                    <Trash2 size={16} />
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section className="panel p-5">
            <h2 className="text-xl font-black">References</h2>
            <p className="mt-2 text-sm font-bold leading-6 text-[#6b767d]">Reference phone and email are private by default and never appear on public profiles.</p>
            <form onSubmit={createReference} className="mt-4 grid gap-3 md:grid-cols-2">
              <input className="field" placeholder="Reference name" value={referenceForm.reference_name} onChange={(event) => setReferenceForm({ ...referenceForm, reference_name: event.target.value })} required />
              <input className="field" placeholder="Reference role" value={referenceForm.reference_role} onChange={(event) => setReferenceForm({ ...referenceForm, reference_role: event.target.value })} />
              <input className="field" placeholder="Organization" value={referenceForm.organization} onChange={(event) => setReferenceForm({ ...referenceForm, organization: event.target.value })} />
              <input className="field" placeholder="Relationship" value={referenceForm.relationship} onChange={(event) => setReferenceForm({ ...referenceForm, relationship: event.target.value })} />
              <input className="field" placeholder="Email (private)" value={referenceForm.email} onChange={(event) => setReferenceForm({ ...referenceForm, email: event.target.value })} />
              <input className="field" placeholder="Phone (private)" value={referenceForm.phone} onChange={(event) => setReferenceForm({ ...referenceForm, phone: event.target.value })} />
              <select className="field" value={referenceForm.visibility} onChange={(event) => setReferenceForm({ ...referenceForm, visibility: event.target.value as "PRIVATE" | "RECRUITERS_ONLY" })}>
                <option value="PRIVATE">Private</option>
                <option value="RECRUITERS_ONLY">Recruiters only</option>
              </select>
              <button className="btn-primary" type="submit">Add reference</button>
              <textarea className="field min-h-20 md:col-span-2" placeholder="Note" value={referenceForm.note} onChange={(event) => setReferenceForm({ ...referenceForm, note: event.target.value })} />
            </form>
            <div className="mt-4 grid gap-2">
              {references.map((item) => (
                <div key={item.id} className="flex flex-col gap-3 rounded-lg bg-white/70 p-3 text-sm font-bold text-[#526069] sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-black text-[#172026]">{item.reference_name}</p>
                    <p>{[item.reference_role, item.organization, item.visibility].filter(Boolean).join(" / ")}</p>
                  </div>
                  <button className="btn-secondary !px-3 !py-2 text-rose-700" type="button" onClick={() => deleteReference(item)}>
                    <Trash2 size={16} />
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
