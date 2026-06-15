"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import BrandLogo from "@/components/BrandLogo";
import { apiFetch, getPostAuthRedirect, saveAuth } from "@/lib/api";
import type { AuthResponse, Role } from "@/types";

type PendingRegistration = {
  email: string;
  role?: Role;
};

export default function VerifyEmailPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queryEmail = params.get("email");
    if (queryEmail) {
      setEmail(queryEmail);
      return;
    }
    const rawPending = window.sessionStorage.getItem("swipe_pending_registration");
    if (!rawPending) return;
    try {
      const pending = JSON.parse(rawPending) as PendingRegistration;
      setEmail(pending.email || "");
    } catch {
      window.sessionStorage.removeItem("swipe_pending_registration");
    }
  }, []);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setTimeout(() => setCooldown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [cooldown]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    try {
      const auth = await apiFetch<AuthResponse>("/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ email, otp })
      });
      window.sessionStorage.removeItem("swipe_pending_registration");
      if (auth.access_token && auth.user) {
        saveAuth(auth);
        toast.success("Email verified successfully. Complete your profile.");
        router.push(getPostAuthRedirect(auth.user.role));
        return;
      }
      window.sessionStorage.setItem("swipe_login_notice", "Email verified successfully. Please log in to complete your profile.");
      toast.success("Email verified successfully. Please log in to complete your profile.");
      router.push("/login");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Email verification failed");
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    if (!email || cooldown > 0) return;
    setResending(true);
    try {
      await apiFetch<{ message: string }>("/auth/resend-email-otp", {
        method: "POST",
        body: JSON.stringify({ email })
      });
      setCooldown(60);
      toast.success("If verification is pending, a new OTP was sent");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not resend OTP");
    } finally {
      setResending(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel soft-panel fade-in-up mx-auto max-w-md p-6 md:p-8">
        <div className="mb-5 flex justify-center">
          <BrandLogo size="auth" priority />
        </div>
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Email verification</p>
        <h1 className="text-3xl font-black tracking-normal">Verify your email</h1>
        <p className="mt-3 text-sm font-medium leading-6 text-[#6b767d]">
          Your account has been created. Enter the OTP sent to your email to activate your profile. OTP expires in 10 minutes.
        </p>
        <div className="mt-6 grid gap-4">
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input id="email" className="field" readOnly value={email} />
          </div>
          <div>
            <label className="label" htmlFor="otp">
              6-digit OTP
            </label>
            <input id="otp" className="field" inputMode="numeric" maxLength={6} minLength={6} required value={otp} onChange={(event) => setOtp(event.target.value)} />
          </div>
          <button className="btn-primary scale-tap" disabled={loading || !email} type="submit">
            {loading && <Loader2 className="animate-spin" size={18} />}
            Verify email
          </button>
          <button className="btn-secondary scale-tap" disabled={resending || cooldown > 0 || !email} onClick={resend} type="button">
            {resending && <Loader2 className="animate-spin" size={18} />}
            {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend OTP"}
          </button>
        </div>
      </form>
    </main>
  );
}
