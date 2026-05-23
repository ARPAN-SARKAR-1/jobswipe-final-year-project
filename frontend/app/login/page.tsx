"use client";

import { BriefcaseBusiness, Crown, Loader2, ShieldCheck, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import toast from "react-hot-toast";

import { apiFetch, roleHome, saveAuth } from "@/lib/api";
import { loginRoleOptions } from "@/lib/options";
import { cx } from "@/lib/utils";
import type { AuthResponse, Role } from "@/types";

const roleIcons = {
  JOB_SEEKER: UserRound,
  RECRUITER: BriefcaseBusiness,
  ADMIN: ShieldCheck,
  OWNER: Crown
} as const;

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role>("JOB_SEEKER");
  const [form, setForm] = useState({ email: "", password: "" });

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    try {
      const auth = await apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ ...form, selected_role: selectedRole })
      });
      saveAuth(auth);
      toast.success("Welcome back");
      router.push(roleHome(auth.user.role));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel mx-auto max-w-2xl p-6 md:p-8">
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Login</p>
        <h1 className="text-3xl font-black tracking-normal">Continue to JobSwipe</h1>
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {loginRoleOptions.map((role) => {
            const Icon = roleIcons[role.value];
            const active = selectedRole === role.value;
            return (
              <button
                key={role.value}
                type="button"
                onClick={() => setSelectedRole(role.value as Role)}
                className={cx(
                  "flex min-h-24 flex-col items-start justify-between rounded-lg border p-4 text-left transition",
                  active ? "border-teal-500 bg-teal-50 text-teal-800 shadow-sm" : "border-black/10 bg-white/75 text-[#526069] hover:border-black/25"
                )}
              >
                <Icon size={20} />
                <span className="text-sm font-black">{role.label}</span>
              </button>
            );
          })}
        </div>
        <div className="mt-6 grid gap-4">
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input id="email" className="field" required type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="password">
              Password
            </label>
            <input id="password" className="field" required type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
          </div>
          <div className="flex justify-end">
            <Link href="/forgot-password" className="text-sm font-black text-teal-700">
              Forgot password?
            </Link>
          </div>
          <button className="btn-primary" disabled={loading} type="submit">
            {loading && <Loader2 className="animate-spin" size={18} />}
            Login
          </button>
        </div>
        <p className="mt-5 text-center text-sm font-bold text-[#6b767d]">
          New here?{" "}
          <Link href="/register" className="text-teal-700">
            Create account
          </Link>
        </p>
      </form>
    </main>
  );
}
