"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import toast from "react-hot-toast";

import { apiFetch, roleHome, saveAuth } from "@/lib/api";
import { roleOptions } from "@/lib/options";
import type { AuthResponse, Role } from "@/types";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm_password: "",
    role: "JOB_SEEKER" as Role,
    accepted_terms: false,
    accepted_privacy: false
  });

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (form.password !== form.confirm_password) {
      toast.error("Password and confirm password must match");
      return;
    }
    if (!form.accepted_terms || !form.accepted_privacy) {
      toast.error("Please accept the Terms and Conditions and Privacy Policy");
      return;
    }
    setLoading(true);
    try {
      const auth = await apiFetch<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(form)
      });
      saveAuth(auth);
      toast.success("Signup successful");
      router.push(roleHome(auth.user.role));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel mx-auto max-w-xl p-6 md:p-8">
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Create account</p>
        <h1 className="text-3xl font-black tracking-normal">Join JobSwipe</h1>
        <div className="mt-6 grid gap-4">
          <div>
            <label className="label" htmlFor="name">
              Name
            </label>
            <input id="name" className="field" required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input id="email" className="field" required type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="password">
                Password
              </label>
              <input id="password" className="field" required minLength={8} type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="confirm_password">
                Confirm password
              </label>
              <input id="confirm_password" className="field" required minLength={8} type="password" value={form.confirm_password} onChange={(event) => setForm({ ...form, confirm_password: event.target.value })} />
            </div>
          </div>
          <div>
            <label className="label" htmlFor="role">
              Role
            </label>
            <select id="role" className="field" value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value as Role })}>
              {roleOptions.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>
          </div>
          <label className="flex items-start gap-3 rounded-lg border border-black/10 bg-white/70 p-3 text-sm font-bold text-[#526069]">
            <input
              className="mt-1 h-4 w-4 accent-teal-600"
              type="checkbox"
              checked={form.accepted_terms}
              onChange={(event) => setForm({ ...form, accepted_terms: event.target.checked, accepted_privacy: event.target.checked })}
            />
            <span>
              I agree to the{" "}
              <Link href="/terms" className="text-teal-700 underline">
                Terms and Conditions
              </Link>
              {" "}and{" "}
              <Link href="/privacy" className="text-teal-700 underline">
                Privacy Policy
              </Link>
              .
            </span>
          </label>
          <button className="btn-primary" disabled={loading} type="submit">
            {loading && <Loader2 className="animate-spin" size={18} />}
            Create account
          </button>
        </div>
        <p className="mt-5 text-center text-sm font-bold text-[#6b767d]">
          Already registered?{" "}
          <Link href="/login" className="text-teal-700">
            Login
          </Link>
        </p>
      </form>
    </main>
  );
}
