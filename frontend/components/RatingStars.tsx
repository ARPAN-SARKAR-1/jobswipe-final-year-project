"use client";

type RatingStarsProps = {
  value: number;
  onChange?: (value: number) => void;
  label?: string;
  size?: "sm" | "md";
};

export default function RatingStars({ value, onChange, label, size = "md" }: RatingStarsProps) {
  const interactive = Boolean(onChange);
  const textSize = size === "sm" ? "text-base" : "text-xl";

  return (
    <div className="grid gap-1">
      {label && <span className="text-xs font-black uppercase tracking-wide text-[#6b767d]">{label}</span>}
      <div className="flex items-center gap-1" aria-label={`${label || "Rating"} ${value} out of 5`}>
        {[1, 2, 3, 4, 5].map((star) => {
          const active = star <= Math.round(value || 0);
          if (interactive) {
            return (
              <button
                key={star}
                type="button"
                className={`${textSize} leading-none ${active ? "text-amber-500" : "text-[#c8d0d5]"}`}
                onClick={() => onChange?.(star)}
                aria-label={`Set ${label || "rating"} to ${star}`}
              >
                ★
              </button>
            );
          }
          return (
            <span key={star} className={`${textSize} leading-none ${active ? "text-amber-500" : "text-[#c8d0d5]"}`}>
              ★
            </span>
          );
        })}
        <span className="ml-2 text-sm font-black text-[#526069]">{Number(value || 0).toFixed(1)}</span>
      </div>
    </div>
  );
}
