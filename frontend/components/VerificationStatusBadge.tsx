import { cx } from "@/lib/utils";

const labels: Record<string, string> = {
  PENDING: "Pending Verification",
  VERIFIED: "Verified",
  REJECTED: "Rejected",
  SUSPENDED: "Suspended",
  STUDENT_UNVERIFIED: "Student Not Verified",
  STUDENT_PENDING: "Student Pending",
  STUDENT_VERIFIED: "Student Verified",
  STUDENT_REJECTED: "Student Rejected",
  GRADUATION_UNVERIFIED: "Graduation Not Verified",
  GRADUATION_PENDING: "Graduation Pending",
  GRADUATION_VERIFIED: "Graduation Verified",
  GRADUATION_REJECTED: "Graduation Rejected",
  EXPERIENCE_UNVERIFIED: "Experience Not Verified",
  EXPERIENCE_PENDING: "Experience Pending",
  EXPERIENCE_VERIFIED: "Experience Verified",
  EXPERIENCE_REJECTED: "Experience Rejected"
};

const styles: Record<string, string> = {
  PENDING: "bg-amber-50 text-amber-800 border-amber-200",
  VERIFIED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  REJECTED: "bg-rose-50 text-rose-700 border-rose-200",
  SUSPENDED: "bg-slate-100 text-slate-700 border-slate-200",
  STUDENT_UNVERIFIED: "bg-slate-100 text-slate-700 border-slate-200",
  STUDENT_PENDING: "bg-amber-50 text-amber-800 border-amber-200",
  STUDENT_VERIFIED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  STUDENT_REJECTED: "bg-rose-50 text-rose-700 border-rose-200",
  GRADUATION_UNVERIFIED: "bg-slate-100 text-slate-700 border-slate-200",
  GRADUATION_PENDING: "bg-amber-50 text-amber-800 border-amber-200",
  GRADUATION_VERIFIED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  GRADUATION_REJECTED: "bg-rose-50 text-rose-700 border-rose-200",
  EXPERIENCE_UNVERIFIED: "bg-slate-100 text-slate-700 border-slate-200",
  EXPERIENCE_PENDING: "bg-amber-50 text-amber-800 border-amber-200",
  EXPERIENCE_VERIFIED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  EXPERIENCE_REJECTED: "bg-rose-50 text-rose-700 border-rose-200"
};

export default function VerificationStatusBadge({ status }: { status: string }) {
  return (
    <span className={cx("rounded-lg border px-2.5 py-1 text-xs font-black", styles[status] || styles.PENDING)}>
      {labels[status] || status.replaceAll("_", " ")}
    </span>
  );
}
