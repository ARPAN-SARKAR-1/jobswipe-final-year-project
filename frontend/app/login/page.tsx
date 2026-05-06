"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import toast from "react-hot-toast";

import { apiFetch, roleHome, saveAuth } from "@/lib/api";
import type { AuthResponse } from "@/types";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    try {
      const auth = await apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(form)
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
      <form onSubmit={submit} className="panel mx-auto max-w-md p-6 md:p-8">
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Login</p>
        <h1 className="text-3xl font-black tracking-normal">Continue to JobSwipe</h1>
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
