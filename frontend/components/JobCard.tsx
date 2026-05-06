import { AlertTriangle, Building2, CalendarClock, IndianRupee, MapPin, MonitorSmartphone } from "lucide-react";
import Link from "next/link";

import BondBadge from "@/components/BondBadge";
import MatchScoreBadge from "@/components/MatchScoreBadge";
import { assetUrl } from "@/lib/api";
import { formatDate, splitSkills } from "@/lib/utils";
import type { Job } from "@/types";

export default function JobCard({ job, actions, detailsHref }: { job: Job; actions?: React.ReactNode; detailsHref?: string }) {
  const logo = assetUrl(job.company_logo_url);
  const skills = job.required_skills_list?.length ? job.required_skills_list : splitSkills(job.required_skills);

  return (
    <article className="panel overflow-hidden p-5">
      <div className="flex items-start gap-4">
        <div className="grid h-14 w-14 shrink-0 place-items-center rounded-lg border border-black/10 bg-white">
          {logo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={logo} alt={job.company_name} className="h-full w-full rounded-lg object-cover" />
          ) : (
            <Building2 className="text-[#172026]" size={24} />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-xl font-black tracking-normal text-[#172026]">{job.title}</h3>
          <p className="mt-1 text-sm font-bold text-[#6b767d]">{job.company_name}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <MatchScoreBadge job={job} />
            {job.existing_application_status && (
              <span className="rounded-lg bg-sky-50 px-2.5 py-1 text-xs font-black text-sky-700">
                Already Applied: {job.existing_application_status}
              </span>
            )}
          </div>
        </div>
      </div>

      {job.moderation_status !== "ACTIVE" && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
          <AlertTriangle className="mt-0.5 shrink-0" size={16} />
          <span>This job is {job.moderation_status.toLowerCase()} by admin{job.moderation_reason ? `: ${job.moderation_reason}` : "."}</span>
        </div>
      )}

      <div className="mt-5 grid gap-2 text-sm font-bold text-[#526069] sm:grid-cols-2">
        <span className="flex items-center gap-2">
          <MapPin size={16} /> {job.location}
        </span>
        <span className="flex items-center gap-2">
          <MonitorSmartphone size={16} /> {job.job_type} / {job.work_mode}
        </span>
        <span className="flex items-center gap-2">
          <IndianRupee size={16} /> {job.salary || "Not disclosed"}
        </span>
        <span className="flex items-center gap-2">
          <CalendarClock size={16} /> Apply by {formatDate(job.deadline)}
        </span>
      </div>

      <div className="mt-4">
        <BondBadge job={job} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {skills.map((skill) => (
          <span key={skill} className="rounded-lg bg-teal-50 px-2.5 py-1 text-xs font-black text-teal-700">
            {skill}
          </span>
        ))}
      </div>
      {job.matched_skills && job.matched_skills.length > 0 && (
        <p className="mt-3 text-xs font-black text-emerald-700">Matched skills: {job.matched_skills.join(", ")}</p>
      )}

      <p className="mt-4 text-sm font-medium leading-6 text-[#526069]">{job.description}</p>
      <p className="mt-3 text-sm font-bold text-[#172026]">Experience: {job.required_experience_level}</p>
      {detailsHref && (
        <Link href={detailsHref} className="mt-4 inline-flex text-sm font-black text-teal-700">
          View details
        </Link>
      )}
      {actions && <div className="mt-5 flex flex-wrap gap-2">{actions}</div>}
    </article>
  );
}
