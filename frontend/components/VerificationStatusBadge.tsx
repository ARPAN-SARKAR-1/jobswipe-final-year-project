import { cx } from "@/lib/utils";

const labels = {
  PENDING: "Pending Verification",
  VERIFIED: "Verified",
  REJECTED: "Rejected"
} as const;

const styles = {
  PENDING: "bg-amber-50 text-amber-800 border-amber-200",
  VERIFIED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  REJECTED: "bg-rose-50 text-rose-700 border-rose-200"
} as const;

export default function VerificationStatusBadge({ status }: { status: keyof typeof labels }) {
  return (
    <span className={cx("rounded-lg border px-2.5 py-1 text-xs font-black", styles[status])}>
      {labels[status]}
    </span>
  );
}
