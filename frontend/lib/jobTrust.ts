export type JobTrustLevel = "HIGH" | "MEDIUM" | "NEEDS_REVIEW";

type JobTrustInput = {
  company_verified?: boolean;
  recruiter_verified?: boolean;
  career_page_url?: string | null;
  career_link_status?: string | null;
  deadline?: string | null;
  is_active?: boolean;
  moderation_status?: string | null;
  salary?: string | null;
  updated_at?: string | null;
};

function hasSalary(value?: string | null) {
  return Boolean(value && !/not disclosed|undisclosed|na|n\/a/i.test(value.trim()));
}

export function getJobTrustSignal(job: JobTrustInput) {
  let score = 0;
  const reasons: string[] = [];
  const today = new Date();
  const deadlineValid = job.deadline ? new Date(job.deadline).getTime() >= today.setHours(0, 0, 0, 0) : false;

  if (job.company_verified) {
    score += 25;
    reasons.push("verified company");
  }
  if (job.recruiter_verified) {
    score += 20;
    reasons.push("verified recruiter");
  }
  if (job.career_page_url) {
    score += job.career_link_status === "LINK_SUSPICIOUS" ? 8 : 20;
    reasons.push("official career link");
  }
  if (deadlineValid && job.is_active && job.moderation_status === "ACTIVE") {
    score += 20;
    reasons.push("active deadline");
  }
  if (hasSalary(job.salary)) {
    score += 10;
    reasons.push("salary shared");
  }
  if (job.updated_at && Date.now() - new Date(job.updated_at).getTime() < 45 * 24 * 60 * 60 * 1000) {
    score += 5;
  }

  const level: JobTrustLevel = score >= 75 ? "HIGH" : score >= 50 ? "MEDIUM" : "NEEDS_REVIEW";
  return {
    score,
    level,
    label: level === "HIGH" ? "High trust" : level === "MEDIUM" ? "Medium trust" : "Needs review",
    reasons,
    salaryWarning: !hasSalary(job.salary) ? "Salary not disclosed" : null
  };
}

export function jobTrustClass(level: JobTrustLevel) {
  if (level === "HIGH") return "bg-emerald-50 text-emerald-700";
  if (level === "MEDIUM") return "bg-sky-50 text-sky-700";
  return "bg-amber-50 text-amber-800";
}
