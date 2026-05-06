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
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "@/components/PageHeader";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { AdminActionLog, AdminRecruiterVerification, Application, ChatThread, Job, Report, Swipe, User } from "@/types";

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
  const [reports, setReports] = useState<Report[]>([]);
  const [swipes, setSwipes] = useState<Swipe[]>([]);
  const [logs, setLogs] = useState<AdminActionLog[]>([]);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState(emptyAdminForm);

  const load = () => {
    Promise.all([
      apiFetch<AdminStats>("/admin/dashboard"),
      apiFetch<User[]>("/admin/users"),
      apiFetch<Job[]>("/admin/jobs"),
      apiFetch<Application[]>("/admin/applications"),
      apiFetch<ChatThread[]>("/admin/chats"),
      apiFetch<AdminRecruiterVerification[]>("/admin/recruiter-verifications"),
      apiFetch<Report[]>("/admin/reports"),
      apiFetch<Swipe[]>("/admin/swipes"),
      isOwner ? apiFetch<User[]>("/admin/admins") : Promise.resolve([]),
      isOwner ? apiFetch<AdminActionLog[]>("/admin/action-logs") : Promise.resolve([])
    ])
      .then(([dashboard, userRows, jobRows, applicationRows, chatRows, verificationRows, reportRows, swipeRows, adminRows, logRows]) => {
        setStats(dashboard);
        setUsers(userRows);
        setJobs(jobRows);
        setApplications(applicationRows);
        setChats(chatRows);
        setVerifications(verificationRows);
        setReports(reportRows);
        setSwipes(swipeRows);
        setAdmins(adminRows);
        setLogs(logRows);
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Admin data failed"));
  };

  useEffect(() => {
    if (!loading && currentUser) load();
  }, [loading, currentUser?.role]);

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
        <RecruiterVerificationTable verifications={verifications} openAction={openAction} />
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
