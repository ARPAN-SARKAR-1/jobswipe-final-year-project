"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import toast from "react-hot-toast";

import BrandLogo from "@/components/BrandLogo";
import CaptchaBox, { type CaptchaValue } from "@/components/CaptchaBox";
import PasswordInput from "@/components/PasswordInput";
import { apiFetch, roleHome, saveAuth } from "@/lib/api";
import { portalOptions } from "@/lib/options";
import type { AuthResponse, Role } from "@/types";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });
  const [selectedPortal, setSelectedPortal] = useState<Role | "">("");
  const [captcha, setCaptcha] = useState<CaptchaValue>({ challengeId: "", answer: "" });

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedPortal) {
      toast.error("Select a portal before logging in");
      return;
    }
    setLoading(true);
    try {
      const auth = await apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          selected_portal: selectedPortal,
          captcha_challenge_id: captcha.challengeId,
          captcha_answer: captcha.answer
        })
      });
      if (auth.requires_email_verification) {
        toast.error(auth.message || "Verify your email before logging in");
        router.push(`/verify-email?email=${encodeURIComponent(auth.user?.email || form.email)}`);
        return;
      }
      if (auth.requires_2fa && auth.login_challenge_id) {
        window.sessionStorage.setItem(
          "swipe_pending_login",
          JSON.stringify({
            email: auth.user?.email || form.email,
            login_challenge_id: auth.login_challenge_id,
            selected_portal: selectedPortal
          })
        );
        toast.success("Enter the OTP sent to your email");
        router.push("/verify-login");
        return;
      }
      saveAuth(auth);
      toast.success("Welcome back");
      router.push(roleHome(auth.user!.role, selectedPortal));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel mx-auto max-w-md p-6 md:p-8">
        <div className="mb-5 flex justify-center">
          <BrandLogo size="auth" priority />
        </div>
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Login</p>
        <h1 className="text-3xl font-black tracking-normal">Continue to Swipe for Success</h1>
        <p className="mt-3 text-sm font-bold leading-6 text-[#6b767d]">
          Owner, Admin, and Recruiter accounts require email OTP verification for secure login.
        </p>
        <div className="mt-6 grid gap-4">
          <div>
            <label className="label">Portal</label>
            <div className="grid grid-cols-2 gap-2">
              {portalOptions.map((portal) => {
                const isSelected = selectedPortal === portal.value;
                return (
                  <button
                    key={portal.value}
                    className={`rounded-lg border px-3 py-3 text-sm font-black transition ${
                      isSelected ? "border-teal-700 bg-teal-700 text-white" : "border-black/10 bg-white/70 text-[#25313a] hover:border-teal-600"
                    }`}
                    disabled={loading}
                    onClick={() => setSelectedPortal(portal.value)}
                    type="button"
                  >
                    {portal.label}
                  </button>
                );
              })}
            </div>
          </div>
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
            <PasswordInput id="password" required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
          </div>
          <div className="flex justify-end">
            <Link href="/forgot-password" className="text-sm font-black text-teal-700">
              Forgot password?
            </Link>
          </div>
          <CaptchaBox disabled={loading} onChange={setCaptcha} purpose="login" />
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
