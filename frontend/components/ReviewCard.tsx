import RatingStars from "@/components/RatingStars";
import { formatDate } from "@/lib/utils";

type ReviewCardProps = {
  reviewerName?: string | null;
  title?: string | null;
  text?: string | null;
  rating: number;
  createdAt: string;
  pros?: string | null;
  cons?: string | null;
  badges?: string[];
};

export default function ReviewCard({ reviewerName, title, text, rating, createdAt, pros, cons, badges = [] }: ReviewCardProps) {
  return (
    <article className="rounded-lg border border-black/10 bg-white/70 p-4">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
        <div>
          <p className="font-black text-[#172026]">{reviewerName || "Anonymous job seeker"}</p>
          {title && <h3 className="mt-1 text-base font-black text-[#172026]">{title}</h3>}
          <p className="mt-1 text-xs font-bold text-[#8a949a]">{formatDate(createdAt)}</p>
        </div>
        <RatingStars value={rating} size="sm" />
      </div>
      {text && <p className="mt-3 text-sm font-medium leading-6 text-[#526069]">{text}</p>}
      {(pros || cons) && (
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {pros && (
            <div className="rounded-lg bg-emerald-50 p-3 text-sm font-bold leading-6 text-emerald-800">
              <span className="block text-xs uppercase text-emerald-700">Pros</span>
              {pros}
            </div>
          )}
          {cons && (
            <div className="rounded-lg bg-amber-50 p-3 text-sm font-bold leading-6 text-amber-800">
              <span className="block text-xs uppercase text-amber-700">Cons</span>
              {cons}
            </div>
          )}
        </div>
      )}
      {badges.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {badges.map((badge) => (
            <span key={badge} className="rounded-full border border-black/10 bg-white px-3 py-1 text-xs font-black text-[#526069]">
              {badge}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}
