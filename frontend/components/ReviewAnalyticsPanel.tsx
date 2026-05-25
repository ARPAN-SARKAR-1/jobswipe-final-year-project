import type { ReviewAnalytics } from "@/types";

type ReviewAnalyticsPanelProps = {
  analytics: ReviewAnalytics | null;
};

function MiniTable({ title, rows }: { title: string; rows: Record<string, unknown>[] }) {
  const labelFor = (row: Record<string, unknown>) => String(row.name || row.company_name || row.recruiter_name || "Review");
  const metricFor = (row: Record<string, unknown>) => {
    const average = typeof row.average_rating === "number" ? row.average_rating.toFixed(1) : "";
    const total = typeof row.total_reviews === "number" ? `(${row.total_reviews})` : "";
    return `${average} ${total}`.trim() || "-";
  };

  return (
    <div className="rounded-lg border border-black/10 bg-white/70 p-4">
      <h3 className="font-black text-[#172026]">{title}</h3>
      <div className="mt-3 grid gap-2">
        {rows.length === 0 ? (
          <p className="text-sm font-bold text-[#6b767d]">No data yet.</p>
        ) : (
          rows.map((row, index) => (
            <div key={`${title}-${index}`} className="flex items-center justify-between gap-3 rounded-lg bg-[#fbfaf7] px-3 py-2 text-sm font-bold">
              <span className="text-[#172026]">{labelFor(row)}</span>
              <span className="text-[#526069]">{metricFor(row)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default function ReviewAnalyticsPanel({ analytics }: ReviewAnalyticsPanelProps) {
  if (!analytics) {
    return (
      <section className="panel p-5">
        <h2 className="text-xl font-black">Review Analytics</h2>
        <p className="mt-2 text-sm font-bold text-[#6b767d]">Loading review analytics...</p>
      </section>
    );
  }

  return (
    <section className="panel p-5">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div>
          <h2 className="text-xl font-black">Review Analytics</h2>
          <p className="mt-1 text-sm font-bold text-[#6b767d]">Company and recruiter trust signals from candidate feedback.</p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs font-black">
          <span className="rounded-full bg-amber-100 px-3 py-1 text-amber-800">{analytics.flagged_reviews_count} flagged</span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">{analytics.hidden_reviews_count} hidden</span>
        </div>
      </div>
      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <MiniTable title="Highest Rated Companies" rows={analytics.highest_rated_companies} />
        <MiniTable title="Lowest Rated Companies" rows={analytics.lowest_rated_companies} />
        <MiniTable title="Most Reviewed Companies" rows={analytics.most_reviewed_companies} />
        <MiniTable title="Recruiters Needing Attention" rows={analytics.low_rated_recruiters} />
      </div>
    </section>
  );
}
