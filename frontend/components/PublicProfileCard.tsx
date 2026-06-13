import { Building2, FileText, Lock, UserRound } from "lucide-react";
import Link from "next/link";

import ProfileShareButton from "@/components/ProfileShareButton";
import VerifiedBadge from "@/components/VerifiedBadge";
import { assetUrl } from "@/lib/api";
import type { PublicProfile } from "@/types";

export default function PublicProfileCard({ profile, shareHref }: { profile: PublicProfile; shareHref: string }) {
  const avatar = assetUrl(profile.profile_picture_url);
  const companyHref = profile.company?.slug || profile.company?.public_company_id || profile.company?.id;

  return (
    <section className="panel p-5">
      <div className="flex flex-col gap-5 md:flex-row md:items-start">
        <div className="grid h-28 w-28 shrink-0 place-items-center overflow-hidden rounded-lg border border-black/10 bg-white">
          {avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={avatar} alt={profile.name} className="h-full w-full object-cover" />
          ) : (
            <UserRound size={30} />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-black text-[#172026]">{profile.name}</h1>
            <VerifiedBadge label={profile.verification_label || "Verified profile"} verified={profile.verified_profile} />
          </div>
          <div className="mt-2 flex flex-wrap gap-2 text-xs font-black text-[#526069]">
            <span className="rounded-lg bg-white px-2.5 py-1">{profile.role.replaceAll("_", " ")}</span>
            <span className="rounded-lg bg-white px-2.5 py-1">ID {profile.public_user_id}</span>
            {profile.username && <span className="rounded-lg bg-white px-2.5 py-1">@{profile.username}</span>}
          </div>
          {profile.is_limited ? (
            <p className="mt-4 flex items-center gap-2 text-sm font-bold text-[#6b767d]">
              <Lock size={16} />
              This profile is private.
            </p>
          ) : (
            <>
              {profile.bio && <p className="mt-4 max-w-3xl text-sm font-medium leading-6 text-[#526069]">{profile.bio}</p>}
              {profile.company && (
                <div className="mt-4 rounded-lg border border-black/10 bg-white/70 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Building2 size={16} />
                    {companyHref ? (
                      <Link href={`/companies/${companyHref}`} className="font-black text-teal-700">
                        {profile.company.name || "Company"}
                      </Link>
                    ) : (
                      <span className="font-black">{profile.company.name || "Company"}</span>
                    )}
                    <VerifiedBadge label="Verified company" verified={profile.company.company_verified} />
                    <VerifiedBadge label="Verified recruiter" verified={profile.company.recruiter_verified} />
                  </div>
                  {profile.company.designation && <p className="mt-1 text-sm font-bold text-[#6b767d]">{profile.company.designation}</p>}
                </div>
              )}
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                {[
                  ["Education", [profile.degree, profile.education, profile.college].filter(Boolean).join(" / ")],
                  ["Experience", profile.experience_level],
                  ["Preferred location", profile.preferred_location],
                  ["Preferred job type", profile.preferred_job_type]
                ]
                  .filter(([, value]) => value)
                  .map(([label, value]) => (
                    <div key={label} className="rounded-lg bg-white/70 p-3">
                      <p className="text-xs font-black uppercase text-[#8a949a]">{label}</p>
                      <p className="mt-1 font-bold text-[#172026]">{value}</p>
                    </div>
                  ))}
              </div>
              {profile.skills_list.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {profile.skills_list.map((skill) => (
                    <span key={skill} className="rounded-lg bg-teal-50 px-2.5 py-1 text-xs font-black text-teal-700">
                      {skill}
                    </span>
                  ))}
                </div>
              )}
              {profile.public_documents.length > 0 && (
                <div className="mt-5">
                  <h2 className="text-base font-black">Public certificates</h2>
                  <div className="mt-2 grid gap-2">
                    {profile.public_documents.map((document) => (
                      <div key={document.id} className="flex items-center gap-2 rounded-lg bg-white/70 p-3 text-sm font-bold text-[#526069]">
                        <FileText size={16} />
                        <span>{document.title}</span>
                        <VerifiedBadge label="Verified document" verified={document.verification_status === "VERIFIED"} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
          <div className="mt-5 flex flex-wrap gap-2">
            <ProfileShareButton href={shareHref} />
          </div>
        </div>
      </div>
    </section>
  );
}
