import { ShieldCheck } from "lucide-react";

import { formatBondYears } from "@/lib/utils";
import type { Job } from "@/types";

export default function BondBadge({ job, compact = false }: { job: Pick<Job, "has_bond" | "bond_years" | "bond_details">; compact?: boolean }) {
  const label = job.has_bond ? `Bond: ${formatBondYears(job.bond_years)}` : "No bond";
  return (
    <div
      className={
        job.has_bond
          ? "inline-flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-black text-amber-800"
          : "inline-flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-black text-emerald-700"
      }
    >
      <ShieldCheck size={14} />
      <span>{label}</span>
      {!compact && job.has_bond && job.bond_details ? <span className="hidden font-bold text-amber-700 sm:inline">- {job.bond_details}</span> : null}
    </div>
  );
}
