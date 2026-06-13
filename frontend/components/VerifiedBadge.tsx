import { BadgeCheck } from "lucide-react";

export default function VerifiedBadge({ label, verified }: { label: string; verified?: boolean }) {
  if (!verified) return null;
  return (
    <span title={label} className="inline-flex items-center gap-1 rounded-lg bg-sky-50 px-2 py-1 text-xs font-black text-sky-700">
      <BadgeCheck size={14} />
      {label}
    </span>
  );
}
