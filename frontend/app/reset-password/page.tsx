"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import { apiFetch } from "@/lib/api";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ token: "", new_password: "", confirm_new_password: "" });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) setForm((current) => ({ ...current, token }));
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (form.new_password !== form.confirm_new_password) {
      toast.error("New password and confirm password must match");
      return;
    }
    setLoading(true);
    try {
      await apiFetch<{ message: string }>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify(form)
      });
      toast.success("Password reset successful");
      router.push("/login");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Reset failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel mx-auto max-w-md p-6 md:p-8">
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Reset</p>
        <h1 className="text-3xl font-black tracking-normal">Set new password</h1>
        <div className="mt-6 grid gap-4">
          <div>
            <label className="label" htmlFor="token">
              Token
            </label>
            <input id="token" className="field" required value={form.token} onChange={(event) => setForm({ ...form, token: event.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="new_password">
              New password
            </label>
            <input id="new_password" className="field" minLength={8} required type="password" value={form.new_password} onChange={(event) => setForm({ ...form, new_password: event.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="confirm_new_password">
              Confirm new password
            </label>
            <input id="confirm_new_password" className="field" minLength={8} required type="password" value={form.confirm_new_password} onChange={(event) => setForm({ ...form, confirm_new_password: event.target.value })} />
          </div>
          <button className="btn-primary" disabled={loading} type="submit">
            {loading && <Loader2 className="animate-spin" size={18} />}
            Reset password
          </button>
        </div>
      </form>
    </main>
  );
}
