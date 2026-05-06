import type { Job } from "@/types";

export default function MatchScoreBadge({ job }: { job: Job }) {
  if (job.match_score === undefined || job.match_score === null) {
    return job.match_note ? (
      <span className="rounded-lg bg-stone-100 px-2.5 py-1 text-xs font-black text-stone-700">{job.match_note}</span>
    ) : null;
  }

  const tone =
    job.match_score >= 75
      ? "bg-emerald-50 text-emerald-700"
      : job.match_score >= 50
      ? "bg-teal-50 text-teal-700"
      : "bg-amber-50 text-amber-800";

  return <span className={`rounded-lg px-2.5 py-1 text-xs font-black ${tone}`}>Match: {job.match_score}%</span>;
}
