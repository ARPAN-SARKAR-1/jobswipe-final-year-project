"use client";

import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useParams } from "next/navigation";

import EmptyState from "@/components/EmptyState";
import PageHeader from "@/components/PageHeader";
import PublicProfileCard from "@/components/PublicProfileCard";
import { apiFetch } from "@/lib/api";
import type { PublicProfile } from "@/types";

export default function PublicIdProfilePage() {
  const params = useParams<{ publicUserId: string }>();
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!params.publicUserId) return;
    setLoading(true);
    apiFetch<PublicProfile>(`/profiles/id/${params.publicUserId}`)
      .then(setProfile)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Profile failed to load"))
      .finally(() => setLoading(false));
  }, [params.publicUserId]);

  if (loading) return <main className="page-shell">Loading profile...</main>;
  if (!profile) return <main className="page-shell"><EmptyState title="Profile unavailable" text="This profile could not be loaded." /></main>;

  return (
    <main className="page-shell">
      <PageHeader title="Public Profile" eyebrow="Swipe for Success" />
      <PublicProfileCard profile={profile} shareHref={profile.username ? `/u/${profile.username}` : `/u/id/${profile.public_user_id}`} />
    </main>
  );
}
