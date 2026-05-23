import { BadgeCheck } from "lucide-react";

export default function BlueTick({ label = "Verified" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-lg border border-sky-200 bg-sky-50 px-2.5 py-1 text-xs font-black text-sky-700">
      <BadgeCheck size={14} />
      {label}
    </span>
  );
}
