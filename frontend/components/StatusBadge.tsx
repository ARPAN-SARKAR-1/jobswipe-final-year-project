import { cx } from "@/lib/utils";

const styles: Record<string, string> = {
  APPLIED: "bg-teal-50 text-teal-700 border-teal-200",
  VIEWED: "bg-sky-50 text-sky-700 border-sky-200",
  SHORTLISTED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  REJECTED: "bg-rose-50 text-rose-700 border-rose-200",
  WITHDRAWN: "bg-stone-100 text-stone-700 border-stone-200",
  ACTIVE: "bg-emerald-50 text-emerald-700 border-emerald-200",
  SUSPENDED: "bg-rose-50 text-rose-700 border-rose-200",
  PAUSED: "bg-amber-50 text-amber-800 border-amber-200",
  CLOSED: "bg-stone-100 text-stone-700 border-stone-200",
  REMOVED: "bg-stone-100 text-stone-700 border-stone-200",
  PENDING: "bg-amber-50 text-amber-800 border-amber-200",
  REVIEWED: "bg-sky-50 text-sky-700 border-sky-200",
  RESOLVED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  DISMISSED: "bg-stone-100 text-stone-700 border-stone-200",
  OWNER: "bg-[#172026] text-white border-[#172026]",
  ADMIN: "bg-sky-50 text-sky-700 border-sky-200",
  RECRUITER: "bg-indigo-50 text-indigo-700 border-indigo-200",
  JOB_SEEKER: "bg-teal-50 text-teal-700 border-teal-200",
  PROTECTED: "bg-amber-50 text-amber-800 border-amber-200"
};

export default function StatusBadge({ status }: { status: string }) {
  return <span className={cx("rounded-lg border px-2.5 py-1 text-xs font-black", styles[status] || styles.APPLIED)}>{status}</span>;
}
