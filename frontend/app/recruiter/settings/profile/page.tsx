"use client";

import { Loader2, Settings } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import FileUploadField from "@/components/FileUploadField";
import PageHeader from "@/components/PageHeader";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch } from "@/lib/api";
import { uploadRules, validateFile } from "@/lib/fileValidation";
import { useAuth } from "@/hooks/useAuth";
import type { PublicProfile, UserDocument } from "@/types";

export default function RecruiterProfileSettingsPage() {
  const { loading } = useAuth(["RECRUITER"]);
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [documents, setDocuments] = useState<UserDocument[]>([]);
  const [username, setUsername] = useState("");
  const [bio, setBio] = useState("");
  const [visibility, setVisibility] = useState<"PUBLIC" | "PRIVATE">("PUBLIC");
  const [saving, setSaving] = useState(false);
  const [documentType, setDocumentType] = useState("government_id");

  const load = () => {
    Promise.all([apiFetch<PublicProfile>("/profiles/me"), apiFetch<UserDocument[]>("/profiles/me/documents")])
      .then(([profileData, documentRows]) => {
        setProfile(profileData);
        setDocuments(documentRows);
        setUsername(profileData.username || "");
        setBio(profileData.bio || "");
        setVisibility(profileData.profile_visibility);
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
      if (username.trim() && username.trim() !== profile?.username) {
        await apiFetch<PublicProfile>("/profiles/me/username", {
          method: "PUT",
          body: JSON.stringify({ username: username.trim() })
        });
      }
      await apiFetch<PublicProfile>("/profiles/me/settings", {
        method: "PUT",
        body: JSON.stringify({ bio, profile_visibility: visibility })
      });
      toast.success("Profile settings saved");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const uploadDocument = async (file: File | undefined) => {
    if (!file) return;
    const validationError = validateFile(file, uploadRules.verificationDocument);
    if (validationError) return toast.error(validationError);
    const body = new FormData();
    body.append("document_type", documentType);
    body.append("is_public", "false");
    body.append("file", file);
    try {
      await apiFetch<UserDocument>("/profiles/me/documents", { method: "POST", body });
      toast.success("Private verification document uploaded");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Document upload failed");
    }
  };

  if (loading || !profile) return <main className="page-shell">Loading recruiter settings...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Profile Settings" eyebrow="Recruiter">
        <Link className="btn-secondary !py-2" href="/recruiter/company">
          <Settings size={17} />
          Company settings
        </Link>
      </PageHeader>
      <div className="grid gap-5 lg:grid-cols-[1fr_420px]">
        <form onSubmit={submit} className="panel grid gap-4 p-5">
          <div className="grid gap-4 md:grid-cols-2">
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
          </div>
          <div>
            <label className="label" htmlFor="bio">About</label>
            <textarea id="bio" className="field min-h-36" value={bio} onChange={(event) => setBio(event.target.value)} />
          </div>
          <button className="btn-primary" disabled={saving} type="submit">
            {saving && <Loader2 className="animate-spin" size={18} />}
            Save settings
          </button>
        </form>

        <aside className="panel p-5">
          <h2 className="text-xl font-black">Recruiter Verification</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            <VerificationStatusBadge status={profile.company?.recruiter_verification_status || "PENDING"} />
            <VerificationStatusBadge status={profile.company?.verification_status || "PENDING"} />
          </div>
          <p className="mt-3 text-sm font-bold leading-6 text-[#6b767d]">
            Upload private KYC and company authorization documents. These files are visible only to Owner/Admin reviewers.
          </p>
          <div className="mt-4 grid gap-3">
            <select className="field" value={documentType} onChange={(event) => setDocumentType(event.target.value)}>
              {["government_id", "company_authorization", "hr_proof", "work_email_proof", "company_id_card", "certificate"].map((item) => (
                <option key={item} value={item}>{item.replaceAll("_", " ")}</option>
              ))}
            </select>
            <FileUploadField
              label="Private verification file"
              buttonLabel="Upload private document"
              rule={uploadRules.verificationDocument}
              helper="These files are visible only to authorized reviewers."
              onValidFile={uploadDocument}
            />
          </div>
          <div className="mt-4 grid gap-2">
            {documents.map((document) => (
              <div key={document.id} className="rounded-lg bg-white/70 p-3 text-sm font-bold text-[#526069]">
                {document.document_type.replaceAll("_", " ")} / {document.verification_status}
              </div>
            ))}
          </div>
        </aside>
      </div>
    </main>
  );
}
