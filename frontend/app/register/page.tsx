"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import toast from "react-hot-toast";

import BrandLogo from "@/components/BrandLogo";
import CaptchaBox, { type CaptchaValue } from "@/components/CaptchaBox";
import PasswordInput from "@/components/PasswordInput";
import { ApiError, apiFetch, getPostAuthRedirect, saveAuth } from "@/lib/api";
import { roleOptions } from "@/lib/options";
import type { AuthResponse, Role } from "@/types";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [captcha, setCaptcha] = useState<CaptchaValue>({ challengeId: "", answer: "" });
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
        body: JSON.stringify({
          ...form,
          captcha_challenge_id: captcha.challengeId,
          captcha_answer: captcha.answer
        })
      });
      if (auth.requires_email_verification) {
        const pendingEmail = auth.user?.email || form.email;
        window.sessionStorage.setItem("swipe_pending_registration", JSON.stringify({ email: pendingEmail, role: form.role }));
        toast.success("Account created successfully. Please verify your email to continue.");
        router.push(`/verify-email?email=${encodeURIComponent(pendingEmail)}`);
        return;
      }
      saveAuth(auth);
      toast.success("Account created successfully. Complete your profile.");
      router.push(getPostAuthRedirect(auth.user!.role));
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        toast.error("An account already exists with this email. Please log in.");
      } else if (error instanceof ApiError && error.status >= 500) {
        toast.error("Account could not be created because the verification email could not be sent. Please try again later.");
      } else {
        toast.error(error instanceof Error ? error.message : "Signup failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel mx-auto max-w-xl p-6 md:p-8">
        <div className="mb-5 flex justify-center">
          <BrandLogo size="auth" priority />
        </div>
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Create account</p>
        <h1 className="text-3xl font-black tracking-normal">Join Swipe for Success</h1>
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
              <PasswordInput id="password" required minLength={8} value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="confirm_password">
                Confirm password
              </label>
              <PasswordInput id="confirm_password" required minLength={8} value={form.confirm_password} onChange={(event) => setForm({ ...form, confirm_password: event.target.value })} />
            </div>
          </div>
          <div>
            <label className="label">Account type</label>
            <div className="grid gap-2 sm:grid-cols-2">
              {roleOptions.map((role) => (
                <button
                  key={role.value}
                  className={`rounded-lg border px-3 py-3 text-sm font-black transition ${
                    form.role === role.value ? "border-teal-700 bg-teal-700 text-white" : "border-black/10 bg-white/70 text-[#25313a] hover:border-teal-600"
                  }`}
                  disabled={loading}
                  onClick={() => setForm({ ...form, role: role.value as Role })}
                  type="button"
                >
                  Join as {role.label}
                </button>
              ))}
            </div>
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
          <CaptchaBox disabled={loading} onChange={setCaptcha} purpose="signup" />
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
