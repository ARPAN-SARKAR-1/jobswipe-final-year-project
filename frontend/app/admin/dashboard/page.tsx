"use client";

import {
  Ban,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  MessageCircle,
  PauseCircle,
  PlusCircle,
  Radio,
  ShieldAlert,
  UserRound,
  UsersRound
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import ListToolbar from "@/components/ListToolbar";
import PageHeader from "@/components/PageHeader";
import PaginationControls from "@/components/PaginationControls";
import PasswordInput from "@/components/PasswordInput";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch } from "@/lib/api";
import { paginateItems, textMatches } from "@/lib/listing";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { AdminActionLog, AdminRecruiterVerification, Application, ChatThread, CompanyReview, Job, PaginatedResponse, RecruiterCompanyMember, Report, Swipe, User, UserDocument } from "@/types";

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
  bodyKey?: "reason" | "admin_note";
  fixedBody?: Record<string, string>;
  label?: string;
};

type JobSeekerVerificationQueueItem = {
  id: number;
  public_user_id?: string | null;
  username?: string | null;
  name: string;
  email: string;
  account_status: "ACTIVE" | "SUSPENDED";
  job_seeker_category?: string | null;
  college_name?: string | null;
  university_name?: string | null;
  current_or_last_company?: string | null;
  verification_status?: string | null;
  student_verification_status?: string | null;
  graduation_verification_status?: string | null;
  experience_verification_status?: string | null;
  document_count: number;
  pending_document_count: number;
};

const emptyAdminForm = { name: "", email: "", password: "", confirm_password: "" };

export default function AdminDashboardPage() {
  const { user: currentUser, loading } = useAuth(["ADMIN", "OWNER"]);
  const isOwner = currentUser?.role === "OWNER";
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [admins, setAdmins] = useState<User[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [chats, setChats] = useState<ChatThread[]>([]);
  const [verifications, setVerifications] = useState<AdminRecruiterVerification[]>([]);
  const [companyVerifications, setCompanyVerifications] = useState<AdminRecruiterVerification[]>([]);
  const [memberships, setMemberships] = useState<RecruiterCompanyMember[]>([]);
  const [jobseekerVerifications, setJobseekerVerifications] = useState<JobSeekerVerificationQueueItem[]>([]);
  const [userDocuments, setUserDocuments] = useState<UserDocument[]>([]);
  const [suspiciousJobs, setSuspiciousJobs] = useState<Job[]>([]);
  const [companyReviews, setCompanyReviews] = useState<CompanyReview[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [swipes, setSwipes] = useState<Swipe[]>([]);
  const [logs, setLogs] = useState<AdminActionLog[]>([]);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState(emptyAdminForm);
  const [userQuery, setUserQuery] = useState("");
  const [userRole, setUserRole] = useState("");
  const [userStatus, setUserStatus] = useState("");
  const [userProtection, setUserProtection] = useState("");
  const [userEmailVerified, setUserEmailVerified] = useState("");
  const [userSort, setUserSort] = useState("created_at:desc");
  const [userPage, setUserPage] = useState(1);
  const [userPageSize, setUserPageSize] = useState(20);
  const [userTotal, setUserTotal] = useState(0);

  const load = () => {
    Promise.all([
      apiFetch<AdminStats>("/admin/dashboard"),
      apiFetch<Job[]>("/admin/jobs"),
      apiFetch<Application[]>("/admin/applications"),
      apiFetch<ChatThread[]>("/admin/chats"),
      apiFetch<AdminRecruiterVerification[]>("/admin/recruiter-verifications"),
      apiFetch<AdminRecruiterVerification[]>("/admin/company-verifications"),
      apiFetch<RecruiterCompanyMember[]>("/admin/recruiter-memberships"),
      apiFetch<JobSeekerVerificationQueueItem[]>("/admin/jobseekers/verification-queue"),
      apiFetch<UserDocument[]>("/admin/user-documents"),
      apiFetch<Job[]>("/admin/suspicious-jobs"),
      apiFetch<CompanyReview[]>("/admin/company-reviews"),
      apiFetch<Report[]>("/admin/reports"),
      apiFetch<Swipe[]>("/admin/swipes"),
      isOwner ? apiFetch<User[]>("/admin/admins") : Promise.resolve([]),
      isOwner ? apiFetch<AdminActionLog[]>("/admin/action-logs") : Promise.resolve([])
    ])
      .then(([dashboard, jobRows, applicationRows, chatRows, verificationRows, companyRows, membershipRows, jobseekerRows, documentRows, suspiciousRows, reviewRows, reportRows, swipeRows, adminRows, logRows]) => {
        setStats(dashboard);
        setJobs(jobRows);
        setApplications(applicationRows);
        setChats(chatRows);
        setVerifications(verificationRows);
        setCompanyVerifications(companyRows);
        setMemberships(membershipRows);
        setJobseekerVerifications(jobseekerRows);
        setUserDocuments(documentRows);
        setSuspiciousJobs(suspiciousRows);
        setCompanyReviews(reviewRows);
        setReports(reportRows);
        setSwipes(swipeRows);
        setAdmins(adminRows);
        setLogs(logRows);
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Admin data failed"));
  };

  const loadUsers = () => {
    const [sortBy, sortOrder] = userSort.split(":");
    const params = new URLSearchParams({
      sort_by: sortBy,
      sort_order: sortOrder || "desc",
      page: String(userPage),
      page_size: String(userPageSize)
    });
    if (userQuery) params.set("q", userQuery);
    if (userRole) params.set("role", userRole);
    if (userStatus) params.set("status", userStatus);
    if (userProtection) params.set("protection", userProtection);
    if (userEmailVerified) params.set("email_verified", userEmailVerified);
    apiFetch<PaginatedResponse<User>>(`/admin/users/search?${params.toString()}`)
      .then((result) => {
        setUsers(result.items);
        setUserTotal(result.total);
        setUserPage(result.page);
        setUserPageSize(result.page_size);
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Users failed"));
  };

  useEffect(() => {
    if (!loading && currentUser) load();
  }, [loading, currentUser?.role]);

  useEffect(() => {
    if (!loading && currentUser) loadUsers();
  }, [loading, currentUser?.role, userQuery, userRole, userStatus, userProtection, userEmailVerified, userSort, userPage, userPageSize]);

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
      loadUsers();
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
      loadUsers();
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
          <ListToolbar
            searchValue={userQuery}
            onSearchChange={(value) => {
              setUserQuery(value);
              setUserPage(1);
            }}
            searchPlaceholder="Search name, email, username, or public ID"
            filters={[
              { label: "Role", value: userRole, allLabel: "All roles", options: ["JOB_SEEKER", "RECRUITER", "ADMIN", "OWNER"].map((role) => ({ label: role, value: role })), onChange: (value) => { setUserRole(value); setUserPage(1); } },
              { label: "Status", value: userStatus, allLabel: "All statuses", options: ["ACTIVE", "SUSPENDED", "PENDING", "REJECTED"].map((status) => ({ label: status, value: status })), onChange: (value) => { setUserStatus(value); setUserPage(1); } },
              { label: "Protection", value: userProtection, allLabel: "All protection", options: [{ label: "Protected", value: "PROTECTED" }, { label: "Normal", value: "NORMAL" }], onChange: (value) => { setUserProtection(value); setUserPage(1); } },
              { label: "Email", value: userEmailVerified, allLabel: "All email states", options: [{ label: "Verified", value: "VERIFIED" }, { label: "Not verified", value: "NOT_VERIFIED" }], onChange: (value) => { setUserEmailVerified(value); setUserPage(1); } }
            ]}
            sortValue={userSort}
            sortOptions={[
              { label: "Newest first", value: "created_at:desc" },
              { label: "Oldest first", value: "created_at:asc" },
              { label: "Name A-Z", value: "name:asc" },
              { label: "Name Z-A", value: "name:desc" },
              { label: "Role", value: "role:asc" },
              { label: "Status", value: "status:asc" }
            ]}
            onSortChange={(value) => {
              setUserSort(value);
              setUserPage(1);
            }}
            onReset={() => {
              setUserQuery("");
              setUserRole("");
              setUserStatus("");
              setUserProtection("");
              setUserEmailVerified("");
              setUserSort("created_at:desc");
              setUserPage(1);
            }}
            resultCount={userTotal}
          />
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
                {users.length === 0 ? (
                  <tr>
                    <td className="p-8 text-center text-sm font-bold text-[#6b767d]" colSpan={6}>
                      No results found for the selected filters.
                    </td>
                  </tr>
                ) : users.map((target) => (
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
          <PaginationControls page={userPage} pageSize={userPageSize} total={userTotal} onPageChange={setUserPage} onPageSizeChange={(value) => { setUserPageSize(value); setUserPage(1); }} />
        </div>

        <ModerationJobsTable jobs={jobs} openAction={openAction} />
        <ModerationApplicationsTable applications={applications} openAction={openAction} />
        <ModerationChatsTable chats={chats} openAction={openAction} />
        <CompanyVerificationTable verifications={companyVerifications} openAction={openAction} />
        <RecruiterVerificationTable verifications={verifications} openAction={openAction} />
        <RecruiterMembershipTable memberships={memberships} openAction={openAction} />
        <JobSeekerVerificationTable users={jobseekerVerifications} openAction={openAction} />
        <UserDocumentsTable documents={userDocuments} openAction={openAction} />
        <SuspiciousJobsTable jobs={suspiciousJobs} openAction={openAction} />
        <CompanyReviewsTable reviews={companyReviews} openAction={openAction} />
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
      {type === "password" ? (
        <PasswordInput id={id} required={required} value={value} onChange={(event) => onChange(event.target.value)} />
      ) : (
        <input id={id} className="field" required={required} type={type} value={value} onChange={(event) => onChange(event.target.value)} />
      )}
    </div>
  );
}

function CompanyVerificationTable({ verifications, openAction }: { verifications: AdminRecruiterVerification[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Pending Company Verification</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1180px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Company</th>
              <th className="p-4">Type</th>
              <th className="p-4">Recruiter</th>
              <th className="p-4">Company Status</th>
              <th className="p-4">Note</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {verifications.map((item) => (
              <tr key={item.id} className="border-t border-black/5">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{item.company_name || "Unnamed company"}</p>
                  <p className="font-bold text-[#6b767d]">{item.website || item.official_email_domain || "-"}</p>
                </td>
                <td className="p-4 font-bold text-[#526069]">{item.company_type}</td>
                <td className="p-4">
                  <p className="font-bold text-[#526069]">{item.recruiter_name}</p>
                  <p className="font-bold text-[#8a949a]">{item.recruiter_email}</p>
                </td>
                <td className="p-4"><VerificationStatusBadge status={item.verification_status} /></td>
                <td className="p-4 font-bold text-[#6b767d]">{item.verification_note || "-"}</td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700" type="button" onClick={() => openAction({ title: "Verify company", message: `Verify ${item.company_name || "this company"}?`, endpoint: `/admin/companies/${item.id}/verify`, success: "Company verified successfully", bodyKey: "admin_note", label: "Verification note" })}>
                      Verify
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Reject company", message: `Reject ${item.company_name || "this company"}?`, endpoint: `/admin/companies/${item.id}/reject`, success: "Company rejected successfully", bodyKey: "admin_note", label: "Rejection note" })}>
                      Reject
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-slate-200 bg-slate-50 text-slate-700" type="button" onClick={() => openAction({ title: "Suspend company", message: `Suspend ${item.company_name || "this company"}?`, endpoint: `/admin/companies/${item.id}/suspend`, success: "Company suspended successfully", bodyKey: "admin_note", label: "Suspension note" })}>
                      Suspend
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

function RecruiterMembershipTable({ memberships, openAction }: { memberships: RecruiterCompanyMember[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Pending Recruiter Verification / Join Requests</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1120px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Recruiter</th>
              <th className="p-4">Company</th>
              <th className="p-4">Designation</th>
              <th className="p-4">Verification</th>
              <th className="p-4">Join Status</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {memberships.map((member) => (
              <tr key={member.id} className="border-t border-black/5">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{member.recruiter_name || member.recruiter_id}</p>
                  <p className="font-bold text-[#6b767d]">{member.work_email || member.recruiter_email || "-"}</p>
                </td>
                <td className="p-4 font-bold text-[#526069]">{member.company_name || member.company_id}</td>
                <td className="p-4 font-bold text-[#526069]">{member.designation || "-"}</td>
                <td className="p-4"><VerificationStatusBadge status={member.verification_status} /></td>
                <td className="p-4"><StatusBadge status={member.company_join_status} /></td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700" type="button" onClick={() => openAction({ title: "Verify recruiter membership", message: "Approve this recruiter membership?", endpoint: `/admin/recruiter-memberships/${member.id}/verify`, success: "Recruiter membership verified", bodyKey: "admin_note", label: "Verification note" })}>
                      Verify
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Reject recruiter membership", message: "Reject this recruiter membership?", endpoint: `/admin/recruiter-memberships/${member.id}/reject`, success: "Recruiter membership rejected", bodyKey: "admin_note", label: "Rejection note" })}>
                      Reject
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-slate-200 bg-slate-50 text-slate-700" type="button" onClick={() => openAction({ title: "Suspend recruiter membership", message: "Suspend this recruiter membership?", endpoint: `/admin/recruiter-memberships/${member.id}/suspend`, success: "Recruiter membership suspended", bodyKey: "admin_note", label: "Suspension note" })}>
                      Suspend
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

function JobSeekerVerificationTable({ users, openAction }: { users: JobSeekerVerificationQueueItem[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Job Seeker Verification Queue</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1280px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Job seeker</th>
              <th className="p-4">Public ID</th>
              <th className="p-4">Category</th>
              <th className="p-4">Claim</th>
              <th className="p-4">Student</th>
              <th className="p-4">Graduation</th>
              <th className="p-4">Experience</th>
              <th className="p-4">Documents</th>
              <th className="p-4">Account</th>
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
                <td className="p-4 font-bold text-[#526069]">{target.public_user_id || "-"}</td>
                <td className="p-4 font-bold text-[#526069]">{target.job_seeker_category?.replaceAll("_", " ") || "-"}</td>
                <td className="p-4 font-bold text-[#526069]">
                  {target.college_name || target.university_name || target.current_or_last_company || "-"}
                </td>
                <td className="p-4"><VerificationStatusBadge status={target.student_verification_status || "STUDENT_UNVERIFIED"} /></td>
                <td className="p-4"><VerificationStatusBadge status={target.graduation_verification_status || "GRADUATION_UNVERIFIED"} /></td>
                <td className="p-4"><VerificationStatusBadge status={target.experience_verification_status || "EXPERIENCE_UNVERIFIED"} /></td>
                <td className="p-4 font-bold text-[#526069]">{target.pending_document_count} pending / {target.document_count} total</td>
                <td className="p-4"><StatusBadge status={target.account_status} /></td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700" type="button" onClick={() => openAction({ title: "Verify job seeker", message: "Verify this job seeker profile?", endpoint: `/admin/jobseekers/${target.id}/verify`, success: "Job seeker verified", bodyKey: "admin_note", label: "Verification note" })}>
                      Verify
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Reject job seeker", message: "Reject this job seeker verification?", endpoint: `/admin/jobseekers/${target.id}/reject`, success: "Job seeker verification rejected", bodyKey: "admin_note", label: "Rejection note" })}>
                      Reject
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-slate-200 bg-slate-50 text-slate-700" type="button" onClick={() => openAction({ title: "Suspend job seeker verification", message: "Suspend this job seeker verification?", endpoint: `/admin/jobseekers/${target.id}/suspend`, success: "Job seeker verification suspended", bodyKey: "admin_note", label: "Suspension note" })}>
                      Suspend
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700" type="button" onClick={() => openAction({ title: "Verify student status", message: "Verify this student status?", endpoint: `/admin/jobseekers/${target.id}/verify-student`, method: "POST", success: "Student status verified", bodyKey: "admin_note", label: "Verification note" })}>
                      Verify student
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Reject student status", message: "Reject this student status?", endpoint: `/admin/jobseekers/${target.id}/reject-student`, method: "POST", success: "Student status rejected", bodyKey: "admin_note", label: "Rejection note" })}>
                      Reject student
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700" type="button" onClick={() => openAction({ title: "Verify graduation", message: "Verify this graduation claim?", endpoint: `/admin/jobseekers/${target.id}/verify-graduation`, method: "POST", success: "Graduation verified", bodyKey: "admin_note", label: "Verification note" })}>
                      Verify graduation
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Reject graduation", message: "Reject this graduation claim?", endpoint: `/admin/jobseekers/${target.id}/reject-graduation`, method: "POST", success: "Graduation rejected", bodyKey: "admin_note", label: "Rejection note" })}>
                      Reject graduation
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700" type="button" onClick={() => openAction({ title: "Verify experience", message: "Verify this experience claim?", endpoint: `/admin/jobseekers/${target.id}/verify-experience`, method: "POST", success: "Experience verified", bodyKey: "admin_note", label: "Verification note" })}>
                      Verify experience
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Reject experience", message: "Reject this experience claim?", endpoint: `/admin/jobseekers/${target.id}/reject-experience`, method: "POST", success: "Experience rejected", bodyKey: "admin_note", label: "Rejection note" })}>
                      Reject experience
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

function UserDocumentsTable({ documents, openAction }: { documents: UserDocument[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Private Verification Documents</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1060px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Owner</th>
              <th className="p-4">Document</th>
              <th className="p-4">Visibility</th>
              <th className="p-4">Status</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id} className="border-t border-black/5">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{document.owner_name || `User #${document.owner_user_id}`}</p>
                  <p className="font-bold text-[#6b767d]">{document.owner_email || document.owner_role || "Private verification document"}</p>
                </td>
                <td className="p-4">
                  <p className="font-black text-[#172026]">{document.document_type.replaceAll("_", " ")}</p>
                  <p className="font-bold text-[#6b767d]">{document.original_filename || "-"}</p>
                </td>
                <td className="p-4 font-bold text-[#526069]">{document.visibility.replaceAll("_", " ")}</td>
                <td className="p-4"><VerificationStatusBadge status={document.verification_status} /></td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    {(["VERIFIED", "REJECTED", "PENDING"] as const).map((status) => (
                      <button key={status} className="btn-secondary !px-3 !py-2" type="button" onClick={() => openAction({ title: `${status} document`, message: `Mark this document as ${status.toLowerCase()}?`, endpoint: `/admin/user-documents/${document.id}/review`, success: "Document review updated", fixedBody: { verification_status: status } })}>
                        {status}
                      </button>
                    ))}
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

function SuspiciousJobsTable({ jobs, openAction }: { jobs: Job[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Suspicious Jobs</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Job</th>
              <th className="p-4">Company</th>
              <th className="p-4">Risk Flags</th>
              <th className="p-4">Moderation</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id} className="border-t border-black/5">
                <td className="p-4 font-black text-[#172026]">{job.title}</td>
                <td className="p-4 font-bold text-[#526069]">{job.company_name}</td>
                <td className="p-4 font-bold text-amber-800">{job.risk_flags || "-"}</td>
                <td className="p-4"><StatusBadge status={job.moderation_status} /></td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    <button className="btn-secondary !px-3 !py-2 border-emerald-200 bg-emerald-50 text-emerald-700" type="button" onClick={() => openAction({ title: "Activate suspicious job", message: "Activate this job after review?", endpoint: `/admin/jobs/${job.id}/activate`, success: "Job activated successfully" })}>
                      Activate
                    </button>
                    <button className="btn-secondary !px-3 !py-2 border-rose-200 bg-rose-50 text-rose-700" type="button" onClick={() => openAction({ title: "Remove suspicious job", message: "Remove this suspicious job?", endpoint: `/admin/jobs/${job.id}/remove`, success: "Job removed successfully", bodyKey: "reason", label: "Removal reason" })}>
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

function CompanyReviewsTable({ reviews, openAction }: { reviews: CompanyReview[]; openAction: (action: ConfirmAction) => void }) {
  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">Flagged Company Reviews</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1120px] text-left text-sm">
          <thead className="bg-[#fbfaf7] text-xs font-black uppercase text-[#526069]">
            <tr>
              <th className="p-4">Review</th>
              <th className="p-4">Reviewer</th>
              <th className="p-4">Rating</th>
              <th className="p-4">Status</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {reviews.map((review) => (
              <tr key={review.id} className="border-t border-black/5 align-top">
                <td className="p-4">
                  <p className="font-black text-[#172026]">{review.title}</p>
                  <p className="mt-1 max-w-md font-bold leading-6 text-[#6b767d]">{review.review_text}</p>
                </td>
                <td className="p-4 font-bold text-[#526069]">{review.reviewer_name || review.reviewer_user_id}</td>
                <td className="p-4 font-black text-amber-700">{review.rating}/5</td>
                <td className="p-4"><StatusBadge status={review.moderation_status} /></td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-2">
                    {(["VISIBLE", "HIDDEN", "FLAGGED", "REMOVED"] as const).map((status) => (
                      <button key={status} className="btn-secondary !px-3 !py-2" type="button" onClick={() => openAction({ title: `${status} review`, message: `Mark this review as ${status.toLowerCase()}?`, endpoint: `/admin/company-reviews/${review.id}/moderate`, success: "Review updated successfully", fixedBody: { moderation_status: status } })}>
                        {status}
                      </button>
                    ))}
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
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("default");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const filteredRows = useMemo(() => {
    const matches = rows.filter((row) => textMatches(row, query, [() => row.join(" ")]));
    if (sort === "reverse") return [...matches].reverse();
    return matches;
  }, [rows, query, sort]);
  const pagedRows = useMemo(() => paginateItems(filteredRows, page, pageSize), [filteredRows, page, pageSize]);

  useEffect(() => {
    setPage(1);
  }, [query, sort, pageSize]);

  return (
    <div className="panel overflow-hidden">
      <h2 className="p-5 text-xl font-black">{title}</h2>
      <ListToolbar
        searchValue={query}
        onSearchChange={setQuery}
        searchPlaceholder={`Search ${title.toLowerCase()}`}
        sortValue={sort}
        sortOptions={[
          { label: "Default order", value: "default" },
          { label: "Reverse order", value: "reverse" }
        ]}
        onSortChange={setSort}
        onReset={() => {
          setQuery("");
          setSort("default");
        }}
        resultCount={filteredRows.length}
      />
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
            {pagedRows.length === 0 ? (
              <tr>
                <td className="p-8 text-center text-sm font-bold text-[#6b767d]" colSpan={headers.length}>
                  No results found for the selected filters.
                </td>
              </tr>
            ) : pagedRows.map((row, index) => (
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
      <PaginationControls page={page} pageSize={pageSize} total={filteredRows.length} onPageChange={setPage} onPageSizeChange={setPageSize} />
    </div>
  );
}
