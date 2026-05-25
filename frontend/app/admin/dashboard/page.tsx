"use client";

import {
  Ban,
  Building2,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  Eye,
  EyeOff,
  MessageCircle,
  PauseCircle,
  PlusCircle,
  Radio,
  ShieldAlert,
  Star,
  UserRound,
  UsersRound
} from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
import ReviewAnalyticsPanel from "@/components/ReviewAnalyticsPanel";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type {
  AdminActionLog,
  AdminRecruiterVerification,
  Application,
  CandidateRiskAssessment,
  ChatThread,
  Company,
  CompanyClaim,
  CompanyMember,
  CompanyReview,
  Job,
  JobRiskAssessment,
  RecruiterReview,
  Report,
  ReviewAnalytics,
  SecuritySettings,
  Swipe,
  User,
  UserRiskAssessment
} from "@/types";

type AdminStats = {
  total_users: number;
  total_job_seekers: number;
  total_recruiters: number;
  total_jobs: number;
  active_jobs: number;
  expired_jobs: number;
  total_applications: number;
};

type ConfirmAction = {
  title: string;
  message: string;
  endpoint: string;
  success: string;
  method?: "PUT" | "POST";
  bodyKey?: "reason" | "admin_note" | "note";
  fixedBody?: Record<string, string>;
  label?: string;
};

const emptyAdminForm = { name: "", email: "", password: "", confirm_password: "" };
const PAGE_LIMIT = 20;

export default function AdminDashboardPage() {
  const { user: currentUser, loading } = useAuth(["ADMIN", "OWNER"]);
  const isOwner = currentUser?.role === "OWNER";
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [admins, setAdmins] = useState<User[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [chats, setChats] = useState<ChatThread[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companyClaims, setCompanyClaims] = useState<CompanyClaim[]>([]);
  const [companyMembers, setCompanyMembers] = useState<CompanyMember[]>([]);
  const [verifications, setVerifications] = useState<AdminRecruiterVerification[]>([]);
  const [companyReviews, setCompanyReviews] = useState<CompanyReview[]>([]);
  const [recruiterReviews, setRecruiterReviews] = useState<RecruiterReview[]>([]);
  const [reviewAnalytics, setReviewAnalytics] = useState<ReviewAnalytics | null>(null);
  const [jobRisks, setJobRisks] = useState<JobRiskAssessment[]>([]);
  const [candidateRisks, setCandidateRisks] = useState<CandidateRiskAssessment[]>([]);
  const [userRisks, setUserRisks] = useState<UserRiskAssessment[]>([]);
  const [securitySettings, setSecuritySettings] = useState<SecuritySettings | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [swipes, setSwipes] = useState<Swipe[]>([]);
  const [logs, setLogs] = useState<AdminActionLog[]>([]);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState(emptyAdminForm);
  const [page, setPage] = useState(1);

  const load = () => {
    const pagedQuery = new URLSearchParams({ page: String(page), limit: String(PAGE_LIMIT) }).toString();
    Promise.all([
      apiFetch<AdminStats>("/admin/dashboard"),
      apiFetch<User[]>(`/admin/users?${pagedQuery}`),
      apiFetch<Job[]>(`/admin/jobs?${pagedQuery}`),
      apiFetch<Application[]>(`/admin/applications?${pagedQuery}`),
      apiFetch<ChatThread[]>(`/admin/chats?${pagedQuery}`),
      apiFetch<Company[]>(`/admin/companies?${pagedQuery}`),
      apiFetch<CompanyClaim[]>(`/admin/company-claims?${pagedQuery}`),
      apiFetch<CompanyMember[]>(`/admin/company-members?${new URLSearchParams({ page: String(page), limit: String(PAGE_LIMIT), verification_status: "PENDING" }).toString()}`),
      apiFetch<AdminRecruiterVerification[]>(`/admin/recruiters?${pagedQuery}`),
      apiFetch<CompanyReview[]>(`/admin/company-reviews?${pagedQuery}`),
      apiFetch<RecruiterReview[]>(`/admin/recruiter-reviews?${pagedQuery}`),
      apiFetch<ReviewAnalytics>("/admin/analytics/reviews"),
      apiFetch<JobRiskAssessment[]>(`/admin/risk/jobs?${pagedQuery}`),
      apiFetch<CandidateRiskAssessment[]>(`/admin/risk/candidates?${pagedQuery}`),
      apiFetch<UserRiskAssessment[]>(`/admin/risk/users?${pagedQuery}`),
      apiFetch<SecuritySettings>("/admin/security-settings"),
      apiFetch<Report[]>(`/admin/reports?${pagedQuery}`),
      apiFetch<Swipe[]>(`/admin/swipes?${pagedQuery}`),
      isOwner ? apiFetch<User[]>("/admin/admins") : Promise.resolve([]),
      isOwner ? apiFetch<AdminActionLog[]>("/admin/action-logs") : Promise.resolve([])
    ])
      .then(([dashboard, userRows, jobRows, applicationRows, chatRows, companyRows, claimRows, memberRows, verificationRows, reviewRows, recruiterReviewRows, reviewAnalyticsRows, jobRiskRows, candidateRiskRows, userRiskRows, securityRows, reportRows, swipeRows, adminRows, logRows]) => {
        setStats(dashboard);
        setUsers(userRows);
        setJobs(jobRows);
        setApplications(applicationRows);
        setChats(chatRows);
        setCompanies(companyRows);
        setCompanyClaims(claimRows);
        setCompanyMembers(memberRows);
        setVerifications(verificationRows);
        setCompanyReviews(reviewRows);
        setRecruiterReviews(recruiterReviewRows);
        setReviewAnalytics(reviewAnalyticsRows);
        setJobRisks(jobRiskRows);
        setCandidateRisks(candidateRiskRows);
        setUserRisks(userRiskRows);
        setSecuritySettings(securityRows);
        setReports(reportRows);
        setSwipes(swipeRows);
        setAdmins(adminRows);
        setLogs(logRows);
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Admin data failed"));
  };

  useEffect(() => {
    if (!loading && currentUser) load();
  }, [loading, currentUser?.role, page]);

  const openAction = (action: ConfirmAction) => {
    setReason("");
    setConfirmAction(action);
  };

  const runAction = async () => {
    if (!confirmAction) return;
    if (confirmAction.bodyKey && reason.trim().length < 3) {
      toast.error("Please enter a reason or note");
      return;
    }
    setSubmitting(true);
    try {
      await apiFetch(confirmAction.endpoint, {
        method: confirmAction.method || "PUT",
        body: confirmAction.bodyKey || confirmAction.fixedBody
          ? JSON.stringify({ ...(confirmAction.fixedBody || {}), ...(confirmAction.bodyKey ? { [confirmAction.bodyKey]: reason.trim() } : {}) })
          : undefined
      });
      toast.success(confirmAction.success);
      setConfirmAction(null);
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Admin action failed");
    } finally {
      setSubmitting(false);
    }
  };

  const createAdmin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (createForm.password !== createForm.confirm_password) {
      toast.error("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await apiFetch<User>("/admin/admins", { method: "POST", body: JSON.stringify(createForm) });
      toast.success("Admin created successfully.");
      setCreateForm(emptyAdminForm);
      setCreateOpen(false);
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Only Owner can create admins.");
    } finally {
      setSubmitting(false);
    }
  };

  const roleLabel = (role: User["role"]) => {
    if (role === "OWNER") return "Owner";
    if (role === "ADMIN") return "Admin";
    if (role === "RECRUITER") return "Recruiter";
    return "Job Seeker";
  };

  const canActOnUser = (target: User) => {
    if (!currentUser || target.id === currentUser.id || target.role === "OWNER" || target.is_protected_owner) return false;
    if (currentUser.role === "ADMIN" && target.role === "ADMIN") return false;
    return true;
  };

  const userActionEndpoint = (target: User, action: "suspend" | "activate") => {
    if (target.role === "ADMIN" && isOwner) return `/admin/admins/${target.id}/${action}`;
    return `/admin/users/${target.id}/${action}`;
  };

  const riskReasons = (value?: string | null) => {
    if (!value) return [];
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed.map(String) : [String(parsed)];
    } catch {
      return [value];
    }
  };

  const updateSecuritySetting = async (key: keyof Pick<SecuritySettings, "captcha_login_enabled" | "captcha_signup_enabled" | "captcha_forgot_password_enabled" | "captcha_reports_enabled" | "captcha_company_claims_enabled">, value: boolean) => {
    if (!securitySettings) return;
    const optimistic = { ...securitySettings, [key]: value };
    setSecuritySettings(optimistic);
    try {
      const updated = await apiFetch<SecuritySettings>("/admin/security-settings", {
        method: "PUT",
        body: JSON.stringify({ [key]: value })
      });
      setSecuritySettings(updated);
      toast.success("Security setting updated");
    } catch (error) {
      setSecuritySettings(securitySettings);
      toast.error(error instanceof Error ? error.message : "Security setting failed");
    }
  };

  const hasMoreRows = [users, jobs, applications, chats, companies, companyClaims, companyMembers, verifications, companyReviews, recruiterReviews, jobRisks, candidateRisks, userRisks, reports, swipes].some((rows) => rows.length === PAGE_LIMIT);

  if (loading || !stats || !currentUser) return <main className="page-shell">Loading admin dashboard...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Admin Dashboard" eyebrow={isOwner ? "Owner control" : "Moderation control"}>
        <StatusBadge status={currentUser.role} />
      </PageHeader>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total users" value={stats.total_users} icon={UsersRound} />
        <StatCard label="Job seekers" value={stats.total_job_seekers} icon={UserRound} />
        <StatCard label="Recruiters" value={stats.total_recruiters} icon={BriefcaseBusiness} />
        <StatCard label="Total jobs" value={stats.total_jobs} icon={BriefcaseBusiness} />
        <StatCard label="Active jobs" value={stats.active_jobs} icon={Radio} />
        <StatCard label="Expired jobs" value={stats.expired_jobs} icon={Radio} />
        <StatCard label="Applications" value={stats.total_applications} icon={ClipboardList} />
      </section>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-black/5 bg-white p-3 shadow-sm">
        <span className="text-sm font-black text-[#526069]">Table page {page}</span>
        <div className="flex gap-2">
          <button className="btn-secondary !py-2" type="button" disabled={page === 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>
            Previous
          </button>
          <button className="btn-secondary !py-2" type="button" disabled={!hasMoreRows} onClick={() => setPage((value) => value + 1)}>
            Next
          </button>
        </div>
      </div>

      <section className="mt-7 grid gap-6 lg:grid-cols-2">
        <div className="panel p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black">Security Settings</h2>
              <p className="mt-1 text-sm font-bold text-[#6b767d]">CAPTCHA controls for sensitive flows.</p>
            </div>
            <ShieldAlert className="text-teal-700" size={24} />
          </div>
          {securitySettings && (
            <div className="mt-4 grid gap-3">
              {[
                ["captcha_login_enabled", "Login CAPTCHA"],
                ["captcha_signup_enabled", "Signup CAPTCHA"],
                ["captcha_forgot_password_enabled", "Forgot/reset CAPTCHA"],
                ["captcha_reports_enabled", "Reports CAPTCHA"],
                ["captcha_company_claims_enabled", "Company claims CAPTCHA"]
              ].map(([key, label]) => (
                <label key={key} className="flex items-center justify-between gap-3 rounded-lg border border-black/5 bg-[#fbfaf7] p-3 text-sm font-black text-[#526069]">
                  <span>{label}</span>
                  <input
                    className="h-5 w-5 accent-teal-600"
                    type="checkbox"
                    checked={Boolean(securitySettings[key as keyof SecuritySettings])}
                    onChange={(event) => updateSecuritySetting(key as keyof Pick<SecuritySettings, "captcha_login_enabled" | "captcha_signup_enabled" | "captcha_forgot_password_enabled" | "captcha_reports_enabled" | "captcha_company_claims_enabled">, event.target.checked)}
                  />
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="panel overflow-hidden">
          <div className="p-5">
            <h2 className="text-xl font-black">Suspicious Users</h2>
            <p className="mt-1 text-sm font-bold text-[#6b767d]">Rule-based user risk scoring for fake or spam behavior.</p>
          </div>
          <div className="grid gap-3 p-5 pt-0">
            {userRisks.slice(0, 5).map((risk) => (
              <div key={risk.id} className="rounded-lg border border-black/5 bg-[#fbfaf7] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-black">{risk.user_name || `User #${risk.user_id}`}</p>
                  <StatusBadge status={risk.risk_level} />
                </div>
                <p className="mt-1 text-xs font-bold text-[#6b767d]">{risk.user_email} / {risk.user_role} / score {risk.risk_score}</p>
                <ul className="mt-2 list-disc pl-5 text-xs font-bold leading-5 text-[#526069]">
                  {riskReasons(risk.reasons).slice(0, 2).map((reasonText) => <li key={reasonText}>{reasonText}</li>)}
                </ul>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button className="btn-secondary !py-2" type="button" onClick={() => openAction({ title: "Review user risk", message: "Mark this user risk reviewed?", endpoint: `/admin/risk/users/${risk.user_id}/review`, success: "User risk reviewed", bodyKey: "admin_note" })}>Review</button>
                  {risk.account_status !== "SUSPENDED" ? (
                    <button className="btn-secondary !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Suspend suspicious user", message: `Suspend ${risk.user_name || "this user"}?`, endpoint: `/admin/risk/users/${risk.user_id}/suspend`, success: "User suspended", bodyKey: "reason" })}>Suspend</button>
                  ) : (
                    <button className="btn-secondary !py-2" type="button" onClick={() => openAction({ title: "Activate user", message: `Activate ${risk.user_name || "this user"}?`, endpoint: `/admin/users/${risk.user_id}/activate`, success: "User activated" })}>Activate</button>
                  )}
                </div>
              </div>
            ))}
            {userRisks.length === 0 && <p className="text-sm font-bold text-[#6b767d]">No suspicious users found.</p>}
          </div>
        </div>
      </section>

      <section className="mt-7 grid gap-6 xl:grid-cols-4">
        <div className="panel overflow-hidden">
          <div className="p-5">
            <h2 className="text-xl font-black">Join Requests</h2>
            <p className="mt-1 text-sm font-bold text-[#6b767d]">Pending recruiters waiting for company approval.</p>
          </div>
          <div className="grid gap-3 p-5 pt-0">
            {companyMembers.slice(0, 5).map((member) => (
              <div key={member.id} className="rounded-lg border border-black/5 bg-[#fbfaf7] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-black">{member.user_name || `Recruiter #${member.user_id}`}</p>
                  <VerificationStatusBadge status={member.verification_status} />
                </div>
                <p className="mt-1 text-xs font-bold text-[#6b767d]">{member.company_name} / {member.company_role}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button className="btn-secondary !py-2" type="button" onClick={() => openAction({ title: "Approve join request", message: `Approve ${member.user_name || "this recruiter"} for ${member.company_name || "this company"}?`, endpoint: `/companies/members/${member.id}/approve`, success: "Join request approved", bodyKey: "note" })}>Approve</button>
                  <button className="btn-secondary !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Reject join request", message: `Reject ${member.user_name || "this recruiter"}?`, endpoint: `/companies/members/${member.id}/reject`, success: "Join request rejected", bodyKey: "note" })}>Reject</button>
                </div>
              </div>
            ))}
            {companyMembers.length === 0 && <p className="text-sm font-bold text-[#6b767d]">No recruiter join requests waiting.</p>}
          </div>
        </div>

        <div className="panel overflow-hidden">
          <div className="p-5">
            <h2 className="text-xl font-black">Company Claims</h2>
            <p className="mt-1 text-sm font-bold text-[#6b767d]">Official-domain claims and reserved-name review queue.</p>
          </div>
          <div className="grid gap-3 p-5 pt-0">
            {companyClaims.slice(0, 5).map((claim) => (
              <div key={claim.id} className="rounded-lg border border-black/5 bg-[#fbfaf7] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-black">{claim.requested_company_name}</p>
                  <StatusBadge status={claim.claim_status} />
                </div>
                <p className="mt-1 text-xs font-bold text-[#6b767d]">{claim.official_email} · risk {claim.risk_score}</p>
                {claim.claim_status === "PENDING" && claim.email_verified_at && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button className="btn-secondary !py-2" type="button" onClick={() => openAction({ title: "Approve company claim", message: `Verify ${claim.requested_company_name}?`, endpoint: `/admin/company-claims/${claim.id}/approve`, success: "Company claim approved", bodyKey: "admin_note" })}>Approve</button>
                    <button className="btn-secondary !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Reject company claim", message: `Reject ${claim.requested_company_name}?`, endpoint: `/admin/company-claims/${claim.id}/reject`, success: "Company claim rejected", bodyKey: "admin_note" })}>Reject</button>
                  </div>
                )}
              </div>
            ))}
            {companyClaims.length === 0 && <p className="text-sm font-bold text-[#6b767d]">No company claims waiting.</p>}
          </div>
        </div>

        <div className="panel overflow-hidden">
          <div className="p-5">
            <h2 className="text-xl font-black">Suspicious Jobs</h2>
            <p className="mt-1 text-sm font-bold text-[#6b767d]">Rule-based fake job risk scoring queue.</p>
          </div>
          <div className="grid gap-3 p-5 pt-0">
            {jobRisks.slice(0, 5).map((risk) => (
              <div key={risk.id} className="rounded-lg border border-black/5 bg-[#fbfaf7] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-black">{risk.job_title || `Job #${risk.job_id}`}</p>
                  <StatusBadge status={risk.risk_level} />
                </div>
                <p className="mt-1 text-xs font-bold text-[#6b767d]">{risk.company_name} · score {risk.risk_score} · {risk.moderation_status}</p>
                <ul className="mt-2 list-disc pl-5 text-xs font-bold leading-5 text-[#526069]">
                  {riskReasons(risk.reasons).slice(0, 2).map((reason) => <li key={reason}>{reason}</li>)}
                </ul>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button className="btn-secondary !py-2" type="button" onClick={() => openAction({ title: "Approve job", message: "Approve this flagged job?", endpoint: `/admin/risk/jobs/${risk.job_id}/approve`, success: "Job approved" })}>Approve</button>
                  <button className="btn-secondary !py-2" type="button" onClick={() => openAction({ title: "Pause job", message: "Keep this job paused?", endpoint: `/admin/risk/jobs/${risk.job_id}/pause`, success: "Job paused" })}>Pause</button>
                  <button className="btn-secondary !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Remove job", message: "Remove this job?", endpoint: `/admin/risk/jobs/${risk.job_id}/remove`, success: "Job removed" })}>Remove</button>
                  {risk.recruiter_id && (
                    <button className="btn-secondary !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Suspend recruiter", message: `Suspend ${risk.recruiter_name || "this recruiter"}?`, endpoint: `/admin/users/${risk.recruiter_id}/suspend`, success: "Recruiter suspended", bodyKey: "reason" })}>Suspend Recruiter</button>
                  )}
                </div>
              </div>
            ))}
            {jobRisks.length === 0 && <p className="text-sm font-bold text-[#6b767d]">No suspicious jobs found.</p>}
          </div>
        </div>

        <div className="panel overflow-hidden">
          <div className="p-5">
            <h2 className="text-xl font-black">Suspicious Candidates</h2>
            <p className="mt-1 text-sm font-bold text-[#6b767d]">Candidate reports and profile risk signals.</p>
          </div>
          <div className="grid gap-3 p-5 pt-0">
            {candidateRisks.slice(0, 5).map((risk) => (
              <div key={risk.id} className="rounded-lg border border-black/5 bg-[#fbfaf7] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-black">{risk.job_seeker_name || `Candidate #${risk.job_seeker_id}`}</p>
                  <StatusBadge status={risk.risk_level} />
                </div>
                <p className="mt-1 text-xs font-bold text-[#6b767d]">{risk.job_seeker_email} · score {risk.risk_score}</p>
                <button className="btn-secondary mt-3 !py-2" type="button" onClick={() => openAction({ title: "Review candidate risk", message: "Mark this candidate risk item reviewed?", endpoint: `/admin/risk/candidates/${risk.id}/review`, success: "Candidate risk reviewed", bodyKey: "admin_note" })}>Mark reviewed</button>
              </div>
            ))}
            {candidateRisks.length === 0 && <p className="text-sm font-bold text-[#6b767d]">No suspicious candidates found.</p>}
          </div>
        </div>
      </section>

      <div className="mt-7 grid gap-6">
        {isOwner && (
          <div className="panel overflow-hidden">
            <div className="flex flex-col justify-between gap-3 p-5 md:flex-row md:items-center">
              <div>
                <h2 className="text-xl font-black">Admin Management</h2>
                <p className="mt-1 text-sm font-bold text-[#6b767d]">Owner can create and manage normal admin accounts.</p>
              </div>
              <button className="btn-primary !py-2" type="button" onClick={() => setCreateOpen(true)}>
                <PlusCircle size={17} />
                Create Admin
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
                  <tr>
                    <th className="p-4">Account</th>
                    <th className="p-4">Role</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Protection</th>
                    <th className="p-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {admins.map((admin) => (
                    <tr key={admin.id} className="border-t border-black/5">
                      <td className="p-4">
                        <p className="font-black text-[#172026]">{admin.name}</p>
                        <p className="font-bold text-[#6b767d]">{admin.email}</p>
                      </td>
                      <td className="p-4"><StatusBadge status={admin.role} /></td>
                      <td className="p-4"><StatusBadge status={admin.account_status} /></td>
                      <td className="p-4">{admin.is_protected_owner ? <StatusBadge status="PROTECTED" /> : <span className="font-bold text-[#6b767d]">Normal</span>}</td>
                      <td className="p-4">
                        {canActOnUser(admin) && admin.role === "ADMIN" ? (
                          <div className="flex flex-wrap gap-2">
                            {admin.account_status === "ACTIVE" ? (
                              <button
                                className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                                type="button"
                                onClick={() =>
                                  openAction({
                                    title: "Suspend admin",
                                    message: `Are you sure you want to suspend ${admin.name}?`,
                                    endpoint: `/admin/admins/${admin.id}/suspend`,
                                    success: "Admin suspended successfully",
                                    bodyKey: "reason",
                                    label: "Suspension reason"
                                  })
                                }
                              >
                                <Ban size={15} />
                                Suspend
                              </button>
                            ) : (
                              <button
                                className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700"
                                type="button"
                                onClick={() =>
                                  openAction({
                                    title: "Activate admin",
                                    message: `Are you sure you want to activate ${admin.name}?`,
                                    endpoint: `/admin/admins/${admin.id}/activate`,
                                    success: "Admin activated successfully"
                                  })
                                }
                              >
                                <CheckCircle2 size={15} />
                                Activate
                              </button>
                            )}
                            <button
                              className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                              type="button"
                              onClick={() =>
                                openAction({
                                  title: "Remove admin",
                                  message: `Are you sure you want to remove ${admin.name}?`,
                                  endpoint: `/admin/admins/${admin.id}/remove`,
                                  success: "Admin removed successfully",
                                  bodyKey: "reason",
                                  label: "Removal reason"
                                })
                              }
                            >
                              <ShieldAlert size={15} />
                              Remove
                            </button>
                          </div>
                        ) : (
                          <span className="text-sm font-bold text-[#6b767d]">No actions available</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="panel overflow-hidden">
          <h2 className="p-5 text-xl font-black">Users</h2>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1080px] text-left text-sm">
              <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
                <tr>
                  <th className="p-4">User</th>
                  <th className="p-4">Role</th>
                  <th className="p-4">Account status</th>
                  <th className="p-4">Protection</th>
                  <th className="p-4">Suspension reason</th>
                  <th className="p-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((target) => (
                  <tr key={target.id} className="border-t border-black/5">
                    <td className="p-4">
                      <p className="font-black text-[#172026]">{target.name}</p>
                      <p className="font-bold text-[#6b767d]">{target.email}</p>
                    </td>
                    <td className="p-4"><StatusBadge status={target.role} /></td>
                    <td className="p-4"><StatusBadge status={target.account_status} /></td>
                    <td className="p-4">{target.is_protected_owner ? <StatusBadge status="PROTECTED" /> : <span className="font-bold text-[#6b767d]">Normal</span>}</td>
                    <td className="p-4 font-bold text-[#6b767d]">{target.suspension_reason || "-"}</td>
                    <td className="p-4">
                      {canActOnUser(target) ? (
                        <div className="flex flex-wrap gap-2">
                          {target.account_status === "ACTIVE" ? (
                            <button
                              className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                              type="button"
                              onClick={() =>
                                openAction({
                                  title: "Suspend user",
                                  message: `Are you sure you want to suspend ${target.name}?`,
                                  endpoint: userActionEndpoint(target, "suspend"),
                                  success: target.role === "RECRUITER" ? "Recruiter suspended successfully" : "User suspended successfully",
                                  bodyKey: "reason",
                                  label: "Suspension reason"
                                })
                              }
                            >
                              <Ban size={15} />
                              Suspend
                            </button>
                          ) : (
                            <button
                              className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700"
                              type="button"
                              onClick={() =>
                                openAction({
                                  title: "Activate user",
                                  message: `Are you sure you want to activate ${target.name}?`,
                                  endpoint: userActionEndpoint(target, "activate"),
                                  success: "User activated successfully"
                                })
                              }
                            >
                              <CheckCircle2 size={15} />
                              Activate
                            </button>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm font-bold text-[#6b767d]">No actions available</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <ModerationJobsTable jobs={jobs} openAction={openAction} />
        <ModerationApplicationsTable applications={applications} openAction={openAction} />
        <ModerationChatsTable chats={chats} openAction={openAction} />
        <CompanyVerificationTable companies={companies} openAction={openAction} />
        <RecruiterVerificationTable verifications={verifications} openAction={openAction} />
        <ReviewAnalyticsPanel analytics={reviewAnalytics} />
        <CompanyReviewsTable reviews={companyReviews} openAction={openAction} />
        <RecruiterReviewsTable reviews={recruiterReviews} openAction={openAction} />
        <ReportsTable reports={reports} openAction={openAction} />
        <Table title="Swipes" headers={["ID", "Job seeker", "Job", "Action"]} rows={swipes.map((swipe) => [swipe.id, swipe.job_seeker_id, swipe.job?.title || swipe.job_id, swipe.action])} />

        {isOwner && (
          <Table
            title="Admin Action Logs"
            headers={["ID", "Admin", "Action", "Target", "Reason", "Date"]}
            rows={logs.map((log) => [
              log.id,
              log.admin_id,
              log.action_type,
              `${log.target_type} #${log.target_id}`,
              log.reason || "-",
              formatDate(log.created_at)
            ])}
          />
        )}
      </div>

      {createOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4">
          <form onSubmit={createAdmin} className="w-full max-w-md rounded-lg bg-white p-5 shadow-premium">
            <h2 className="text-xl font-black">Create Admin</h2>
            <div className="mt-4 grid gap-3">
              <Input label="Name" value={createForm.name} onChange={(value) => setCreateForm({ ...createForm, name: value })} required />
              <Input label="Email" type="email" value={createForm.email} onChange={(value) => setCreateForm({ ...createForm, email: value })} required />
              <Input label="Password" type="password" value={createForm.password} onChange={(value) => setCreateForm({ ...createForm, password: value })} required />
              <Input label="Confirm password" type="password" value={createForm.confirm_password} onChange={(value) => setCreateForm({ ...createForm, confirm_password: value })} required />
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button className="btn-secondary" type="button" onClick={() => setCreateOpen(false)}>
                Cancel
              </button>
              <button className="btn-primary" type="submit" disabled={submitting}>
                Create Admin
              </button>
            </div>
          </form>
        </div>
      )}

      {confirmAction && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4">
          <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-premium">
            <h2 className="text-xl font-black">{confirmAction.title}</h2>
            <p className="mt-2 text-sm font-bold leading-6 text-[#6b767d]">{confirmAction.message}</p>
            {confirmAction.bodyKey && (
              <div className="mt-4">
                <label className="label" htmlFor="admin-reason">
                  {confirmAction.label || "Reason"}
                </label>
                <textarea id="admin-reason" className="field min-h-28" value={reason} onChange={(event) => setReason(event.target.value)} />
              </div>
            )}
            <div className="mt-5 flex justify-end gap-2">
              <button className="btn-secondary" type="button" onClick={() => setConfirmAction(null)}>
                Cancel
              </button>
              <button className="btn-primary" type="button" disabled={submitting} onClick={runAction}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

function Input({ label, value, onChange, required, type = "text" }: { label: string; value: string; onChange: (value: string) => void; required?: boolean; type?: string }) {
  const id = label.toLowerCase().replaceAll(" ", "-");
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      <input id={id} className="field" required={required} type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function CompanyVerificationTable({ companies, openAction }: { companies: Company[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <div className="flex items-center gap-2 p-5">
        <Building2 size={19} />
        <h2 className="text-xl font-black">Company Verification</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1180px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Company</th>
              <th className="p-4">Industry</th>
              <th className="p-4">Type</th>
              <th className="p-4">Website</th>
              <th className="p-4">Status</th>
              <th className="p-4">Note</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {companies.map((company) => (
              <tr key={company.id} className="border-t border-black/5 align-top">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{company.company_name}</p>
                  <p className="font-bold text-[#6b767d]">{company.headquarters_location || "-"}</p>
                  <p className="mt-1 text-xs font-black text-[#8a949a]">{company.recruiter_count} recruiters / {company.active_jobs_count} active jobs</p>
                </td>
                <td className="p-4 font-bold text-[#526069]">{company.industry || "-"}</td>
                <td className="p-4 font-bold text-[#526069]">{company.company_type}</td>
                <td className="p-4 font-bold text-[#526069]">{company.website || "-"}</td>
                <td className="p-4"><VerificationStatusBadge status={company.verification_status} /></td>
                <td className="p-4 max-w-xs font-bold leading-6 text-[#6b767d]">{company.verification_note || "-"}</td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Verify company",
                          message: `Verify ${company.company_name}?`,
                          endpoint: `/admin/companies/${company.id}/verify`,
                          success: "Company verified successfully",
                          bodyKey: "admin_note",
                          label: "Verification note"
                        })
                      }
                    >
                      <CheckCircle2 size={15} />
                      Verify
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Reject company",
                          message: `Reject ${company.company_name}?`,
                          endpoint: `/admin/companies/${company.id}/reject`,
                          success: "Company rejected successfully",
                          bodyKey: "admin_note",
                          label: "Rejection note"
                        })
                      }
                    >
                      <Ban size={15} />
                      Reject
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RecruiterVerificationTable({ verifications, openAction }: { verifications: AdminRecruiterVerification[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Recruiter Verification</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Recruiter</th>
              <th className="p-4">Company</th>
              <th className="p-4">Website</th>
              <th className="p-4">Company status</th>
              <th className="p-4">Verification</th>
              <th className="p-4">Note</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {verifications.map((item) => (
              <tr key={item.id} className="border-t border-black/5">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{item.recruiter_name}</p>
                  <p className="font-bold text-[#6b767d]">{item.recruiter_email}</p>
                </td>
                <td className="p-4 font-bold text-[#526069]">{item.company_name || "-"}</td>
                <td className="p-4 font-bold text-[#526069]">{item.website || "-"}</td>
                <td className="p-4"><VerificationStatusBadge status={item.verification_status} /></td>
                <td className="p-4"><VerificationStatusBadge status={item.recruiter_verification_status} /></td>
                <td className="p-4 font-bold text-[#6b767d]">{item.verification_note || "-"}</td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Verify recruiter",
                          message: `Verify ${item.recruiter_name}?`,
                          endpoint: `/admin/recruiters/${item.recruiter_id}/verify`,
                          success: "Recruiter verified successfully",
                          bodyKey: "admin_note",
                          label: "Verification note"
                        })
                      }
                    >
                      <CheckCircle2 size={15} />
                      Verify
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Reject recruiter",
                          message: `Reject ${item.recruiter_name}?`,
                          endpoint: `/admin/recruiters/${item.recruiter_id}/reject`,
                          success: "Recruiter rejected successfully",
                          bodyKey: "admin_note",
                          label: "Rejection note"
                        })
                      }
                    >
                      <Ban size={15} />
                      Reject
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CompanyReviewsTable({ reviews, openAction }: { reviews: CompanyReview[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <div className="flex items-center gap-2 p-5">
        <Star size={19} />
        <h2 className="text-xl font-black">Company Reviews</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Company</th>
              <th className="p-4">Reviewer</th>
              <th className="p-4">Rating</th>
              <th className="p-4">Review</th>
              <th className="p-4">Visibility</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {reviews.map((review) => (
              <tr key={review.id} className="border-t border-black/5 align-top">
                <td className="p-4 font-bold text-[#526069]">{review.company_name || review.company_id}</td>
                <td className="p-4">
                  <p className="font-black text-[#172026]">{review.reviewer_name || review.job_seeker_id}</p>
                  <p className="font-bold text-[#6b767d]">{review.reviewer_email || ""}</p>
                </td>
                <td className="p-4 font-black text-amber-700">{review.overall_rating} / 5</td>
                <td className="p-4 max-w-sm font-bold leading-6 text-[#6b767d]">
                  <span className="block text-[#172026]">{review.review_title || "-"}</span>
                  {review.review_text || "-"}
                </td>
                <td className="p-4"><StatusBadge status={review.moderation_status} /></td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Hide review",
                          message: "Hide this company review from public company profiles?",
                          endpoint: `/admin/company-reviews/${review.id}/hide`,
                          success: "Review hidden successfully"
                        })
                      }
                    >
                      <EyeOff size={15} />
                      Hide
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Show review",
                          message: "Show this company review publicly again?",
                          endpoint: `/admin/company-reviews/${review.id}/show`,
                          success: "Review shown successfully"
                        })
                      }
                    >
                      <Eye size={15} />
                      Show
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-amber-200 bg-amber-50 text-amber-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Flag review",
                          message: "Flag this company review for moderation?",
                          endpoint: `/admin/company-reviews/${review.id}/flag`,
                          success: "Review flagged successfully"
                        })
                      }
                    >
                      <ShieldAlert size={15} />
                      Flag
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RecruiterReviewsTable({ reviews, openAction }: { reviews: RecruiterReview[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <div className="flex items-center gap-2 p-5">
        <Star size={19} />
        <h2 className="text-xl font-black">Recruiter Reviews</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Recruiter</th>
              <th className="p-4">Reviewer</th>
              <th className="p-4">Rating</th>
              <th className="p-4">Review</th>
              <th className="p-4">Status</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {reviews.map((review) => (
              <tr key={review.id} className="border-t border-black/5 align-top">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{review.recruiter_name || review.recruiter_id}</p>
                  <p className="font-bold text-[#6b767d]">{review.company_name || review.recruiter_email || ""}</p>
                </td>
                <td className="p-4 font-bold text-[#526069]">{review.reviewer_name || review.job_seeker_id}</td>
                <td className="p-4 font-black text-amber-700">{review.overall_rating} / 5</td>
                <td className="p-4 max-w-sm font-bold leading-6 text-[#6b767d]">
                  <span className="block text-[#172026]">{review.review_title || "-"}</span>
                  {review.review_text || "-"}
                </td>
                <td className="p-4"><StatusBadge status={review.moderation_status} /></td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                      type="button"
                      onClick={() => openAction({ title: "Hide recruiter review", message: "Hide this recruiter review?", endpoint: `/admin/recruiter-reviews/${review.id}/hide`, success: "Recruiter review hidden" })}
                    >
                      <EyeOff size={15} />
                      Hide
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700"
                      type="button"
                      onClick={() => openAction({ title: "Show recruiter review", message: "Show this recruiter review publicly?", endpoint: `/admin/recruiter-reviews/${review.id}/show`, success: "Recruiter review shown" })}
                    >
                      <Eye size={15} />
                      Show
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-amber-200 bg-amber-50 text-amber-700"
                      type="button"
                      onClick={() => openAction({ title: "Flag recruiter review", message: "Flag this recruiter review?", endpoint: `/admin/recruiter-reviews/${review.id}/flag`, success: "Recruiter review flagged" })}
                    >
                      <ShieldAlert size={15} />
                      Flag
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReportsTable({ reports, openAction }: { reports: Report[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Reports</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1220px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Report</th>
              <th className="p-4">Job</th>
              <th className="p-4">Recruiter</th>
              <th className="p-4">Reporter</th>
              <th className="p-4">Status</th>
              <th className="p-4">Admin note</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id} className="border-t border-black/5 align-top">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{report.report_type.replaceAll("_", " ")}</p>
                  <p className="mt-1 max-w-xs font-bold leading-6 text-[#6b767d]">{report.description}</p>
                </td>
                <td className="p-4 font-bold text-[#526069]">{report.job_title || report.job_id || "-"}</td>
                <td className="p-4 font-bold text-[#526069]">{report.recruiter_name || report.recruiter_id || "-"}</td>
                <td className="p-4">
                  <p className="font-bold text-[#526069]">{report.reporter_name || report.reporter_id}</p>
                  <p className="font-bold text-[#8a949a]">{report.reporter_email || ""}</p>
                </td>
                <td className="p-4"><StatusBadge status={report.status} /></td>
                <td className="p-4 font-bold text-[#6b767d]">{report.admin_note || "-"}</td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    {(["REVIEWED", "RESOLVED", "DISMISSED"] as const).map((status) => (
                      <button
                        key={status}
                        className="btn-secondary !px-3 !py-2"
                        type="button"
                        onClick={() =>
                          openAction({
                            title: `${status.charAt(0)}${status.slice(1).toLowerCase()} report`,
                            message: `Mark this report as ${status.toLowerCase()}?`,
                            endpoint: `/admin/reports/${report.id}/status`,
                            success: "Report updated successfully",
                            fixedBody: { status }
                          })
                        }
                      >
                        {status}
                      </button>
                    ))}
                    {report.job_id && (
                      <>
                        <button
                          className="btn-secondary !px-3 !py-2 border-amber-200 bg-amber-50 text-amber-800"
                          type="button"
                          onClick={() =>
                            openAction({
                              title: "Pause reported job",
                              message: "Pause this reported job post?",
                              endpoint: `/admin/jobs/${report.job_id}/pause`,
                              success: "Job paused successfully",
                              bodyKey: "reason",
                              label: "Pause reason"
                            })
                          }
                        >
                          Pause Job
                        </button>
                        <button
                          className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                          type="button"
                          onClick={() =>
                            openAction({
                              title: "Remove reported job",
                              message: "Remove this reported job post?",
                              endpoint: `/admin/jobs/${report.job_id}/remove`,
                              success: "Job removed successfully",
                              bodyKey: "reason",
                              label: "Removal reason"
                            })
                          }
                        >
                          Remove Job
                        </button>
                      </>
                    )}
                    {report.recruiter_id && (
                      <button
                        className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                        type="button"
                        onClick={() =>
                          openAction({
                            title: "Suspend reported recruiter",
                            message: "Suspend this recruiter account?",
                            endpoint: `/admin/users/${report.recruiter_id}/suspend`,
                            success: "Recruiter suspended successfully",
                            bodyKey: "reason",
                            label: "Suspension reason"
                          })
                        }
                      >
                        Suspend Recruiter
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ModerationChatsTable({ chats, openAction }: { chats: ChatThread[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <div className="flex items-center gap-2 p-5">
        <MessageCircle size={19} />
        <h2 className="text-xl font-black">Chat Threads</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1080px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Job</th>
              <th className="p-4">Recruiter</th>
              <th className="p-4">Job seeker</th>
              <th className="p-4">Thread status</th>
              <th className="p-4">Application</th>
              <th className="p-4">Created</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {chats.map((chat) => (
              <tr key={chat.id} className="border-t border-black/5">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{chat.job_title || `Job #${chat.job_id}`}</p>
                  <p className="font-bold text-[#6b767d]">{chat.company_name || "-"}</p>
                </td>
                <td className="p-4 font-bold text-[#526069]">{chat.recruiter_name || chat.recruiter_id}</td>
                <td className="p-4 font-bold text-[#526069]">{chat.job_seeker_name || chat.job_seeker_id}</td>
                <td className="p-4"><StatusBadge status={chat.status} /></td>
                <td className="p-4">{chat.application_status ? <StatusBadge status={chat.application_status} /> : "-"}</td>
                <td className="p-4 font-bold text-[#526069]">{formatDate(chat.created_at)}</td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="btn-secondary !px-3 !py-2 border-amber-200 bg-amber-50 text-amber-800"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Pause chat thread",
                          message: "Are you sure you want to pause this chat thread?",
                          endpoint: `/admin/chats/${chat.id}/pause`,
                          success: "Chat paused successfully"
                        })
                      }
                    >
                      <PauseCircle size={15} />
                      Pause
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Activate chat thread",
                          message: "Are you sure you want to activate this chat thread?",
                          endpoint: `/admin/chats/${chat.id}/activate`,
                          success: "Chat activated successfully"
                        })
                      }
                    >
                      <CheckCircle2 size={15} />
                      Activate
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ModerationJobsTable({ jobs, openAction }: { jobs: Job[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Jobs</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Job</th>
              <th className="p-4">Deadline</th>
              <th className="p-4">Active</th>
              <th className="p-4">Moderation</th>
              <th className="p-4">Reason</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id} className="border-t border-black/5">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{job.title}</p>
                  <p className="font-bold text-[#6b767d]">{job.company_name}</p>
                </td>
                <td className="p-4 font-bold">{formatDate(job.deadline)}</td>
                <td className="p-4 font-bold">{job.is_active ? "Yes" : "No"}</td>
                <td className="p-4"><StatusBadge status={job.moderation_status} /></td>
                <td className="p-4 font-bold text-[#6b767d]">{job.moderation_reason || "-"}</td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="btn-secondary !px-3 !py-2 border-amber-200 bg-amber-50 text-amber-800"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Pause job post",
                          message: "Are you sure you want to pause this job post?",
                          endpoint: `/admin/jobs/${job.id}/pause`,
                          success: "Job paused successfully",
                          bodyKey: "reason",
                          label: "Pause reason"
                        })
                      }
                    >
                      <PauseCircle size={15} />
                      Pause
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Activate job post",
                          message: "Are you sure you want to activate this job post?",
                          endpoint: `/admin/jobs/${job.id}/activate`,
                          success: "Job activated successfully"
                        })
                      }
                    >
                      <CheckCircle2 size={15} />
                      Activate
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Remove job post",
                          message: "Are you sure you want to remove this job post?",
                          endpoint: `/admin/jobs/${job.id}/remove`,
                          success: "Job removed successfully",
                          bodyKey: "reason",
                          label: "Removal reason"
                        })
                      }
                    >
                      <ShieldAlert size={15} />
                      Remove
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ModerationApplicationsTable({ applications, openAction }: { applications: Application[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Applications</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Application</th>
              <th className="p-4">Job</th>
              <th className="p-4">User status</th>
              <th className="p-4">Admin status</th>
              <th className="p-4">Admin note</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {applications.map((application) => (
              <tr key={application.id} className="border-t border-black/5">
                <td className="p-4 font-bold">#{application.id}</td>
                <td className="p-4">
                  <p className="font-black text-[#172026]">{application.job?.title || application.job_id}</p>
                  {application.job && application.job.moderation_status !== "ACTIVE" && (
                    <p className="mt-1 font-bold text-amber-700">Job {application.job.moderation_status.toLowerCase()} by admin</p>
                  )}
                </td>
                <td className="p-4"><StatusBadge status={application.status} /></td>
                <td className="p-4"><StatusBadge status={application.admin_status} /></td>
                <td className="p-4 font-bold text-[#6b767d]">{application.admin_note || "-"}</td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="btn-secondary !px-3 !py-2 border-amber-200 bg-amber-50 text-amber-800"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Pause application",
                          message: "Are you sure you want to pause this application?",
                          endpoint: `/admin/applications/${application.id}/pause`,
                          success: "Application paused successfully",
                          bodyKey: "admin_note",
                          label: "Admin note"
                        })
                      }
                    >
                      <PauseCircle size={15} />
                      Pause
                    </button>
                    <button
                      className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700"
                      type="button"
                      onClick={() =>
                        openAction({
                          title: "Activate application",
                          message: "Are you sure you want to activate this application?",
                          endpoint: `/admin/applications/${application.id}/activate`,
                          success: "Application activated successfully"
                        })
                      }
                    >
                      <CheckCircle2 size={15} />
                      Activate
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Table({ title, headers, rows }: { title: string; headers: string[]; rows: Array<Array<string | number>> }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">{title}</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              {headers.map((header) => (
                <th key={header} className="p-4">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index} className="border-t border-black/5">
                {row.map((cell, cellIndex) => (
                  <td key={`${index}-${cellIndex}`} className="p-4 font-bold text-[#526069]">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
