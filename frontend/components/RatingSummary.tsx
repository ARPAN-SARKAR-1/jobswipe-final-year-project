import RatingStars from "@/components/RatingStars";

type RatingSummaryProps = {
  title: string;
  average: number;
  total: number;
  rows: { label: string; value: number }[];
};

function ratingLabel(value: number) {
  if (value >= 4.5) return "Excellent";
  if (value >= 4) return "Very Good";
  if (value >= 3) return "Average";
  return "Needs Attention";
}

export default function RatingSummary({ title, average, total, rows }: RatingSummaryProps) {
  return (
    <section className="panel p-5">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div>
          <h2 className="text-xl font-black">{title}</h2>
          <p className="mt-1 text-sm font-bold text-[#6b767d]">{total} visible review{total === 1 ? "" : "s"}</p>
        </div>
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
          <RatingStars value={average} size="sm" />
          <p className="mt-1 text-sm font-black text-amber-800">{ratingLabel(average)}</p>
        </div>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-2">
        {rows.map((row) => (
          <div key={row.label} className="rounded-lg border border-black/10 bg-white/70 p-3">
            <RatingStars value={row.value} label={row.label} size="sm" />
          </div>
        ))}
      </div>
    </section>
  );
}
