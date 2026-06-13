"use client";

import Link from "next/link";
import { Settings } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import PageHeader from "@/components/PageHeader";
import PublicProfileCard from "@/components/PublicProfileCard";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { PublicProfile } from "@/types";

export default function RecruiterProfilePage() {
  const { loading } = useAuth(["RECRUITER"]);
  const [profile, setProfile] = useState<PublicProfile | null>(null);

  useEffect(() => {
    if (loading) return;
    apiFetch<PublicProfile>("/profiles/me")
      .then(setProfile)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Profile failed to load"));
  }, [loading]);

  if (loading) return <main className="page-shell">Loading profile...</main>;
  if (!profile) return <main className="page-shell"><EmptyState title="Profile unavailable" text="Your profile could not be loaded." /></main>;

  return (
    <main className="page-shell">
      <PageHeader title="Recruiter Profile" eyebrow="Profile preview">
        <Link className="btn-secondary !py-2" href="/recruiter/settings/profile">
          <Settings size={17} />
          Settings
        </Link>
      </PageHeader>
      <PublicProfileCard profile={profile} shareHref={profile.username ? `/u/${profile.username}` : `/u/id/${profile.public_user_id}`} />
    </main>
  );
}
