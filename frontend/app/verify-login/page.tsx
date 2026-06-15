"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import BrandLogo from "@/components/BrandLogo";
import { ApiError, apiFetch, getPostAuthRedirect, saveAuth } from "@/lib/api";
import type { AuthResponse, Role } from "@/types";

type PendingLogin = {
  email: string;
  login_challenge_id: string;
  selected_portal?: Role;
};

export default function VerifyLoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<PendingLogin>({ email: "", login_challenge_id: "" });
  const [otp, setOtp] = useState("");
  const [rememberDevice, setRememberDevice] = useState(false);
  const [resending, setResending] = useState(false);
  const [cooldown, setCooldown] = useState(60);

  useEffect(() => {
    const raw = window.sessionStorage.getItem("swipe_pending_login");
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as PendingLogin;
        setPending(parsed);
        return;
      } catch {
        window.sessionStorage.removeItem("swipe_pending_login");
      }
    }
    const params = new URLSearchParams(window.location.search);
    setPending({
      email: params.get("email") || "",
      login_challenge_id: params.get("challenge") || ""
    });
  }, []);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setTimeout(() => setCooldown((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearTimeout(timer);
  }, [cooldown]);

  const showOtpError = (error: unknown) => {
    const message = error instanceof Error ? error.message : "Verification failed";
    const normalized = message.toLowerCase();
    if (normalized.includes("expired")) {
      toast.error("OTP expired. Please request a new code.");
      return;
    }
    if (normalized.includes("wait")) {
      toast.error(message);
      return;
    }
    if (normalized.includes("attempt") || (error instanceof ApiError && error.status === 429)) {
      toast.error("Too many attempts. Please request a new code.");
      return;
    }
    if (normalized.includes("invalid")) {
      toast.error("Invalid OTP.");
      return;
    }
    toast.error(message);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!pending.login_challenge_id) {
      toast.error("Login verification session expired. Please login again.");
      router.push("/login");
      return;
    }
    setLoading(true);
    try {
      const auth = await apiFetch<AuthResponse>("/auth/verify-login-otp", {
        method: "POST",
        body: JSON.stringify({
          login_challenge_id: pending.login_challenge_id,
          otp,
          remember_device: rememberDevice
        })
      });
      saveAuth(auth);
      window.sessionStorage.removeItem("swipe_pending_login");
      toast.success("Secure login complete");
      router.push(getPostAuthRedirect(auth.user!.role));
    } catch (error) {
      showOtpError(error);
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    if (!pending.login_challenge_id || cooldown > 0) return;
    setResending(true);
    try {
      const response = await apiFetch<{ message: string; login_challenge_id: string }>("/auth/resend-login-otp", {
        method: "POST",
        body: JSON.stringify({ login_challenge_id: pending.login_challenge_id })
      });
      const nextPending = { ...pending, login_challenge_id: response.login_challenge_id };
      setPending(nextPending);
      window.sessionStorage.setItem("swipe_pending_login", JSON.stringify(nextPending));
      setOtp("");
      setCooldown(60);
      toast.success("New OTP sent. Check inbox or spam.");
    } catch (error) {
      showOtpError(error);
    } finally {
      setResending(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel mx-auto max-w-md p-6 md:p-8">
        <div className="mb-5 flex justify-center">
          <BrandLogo size="auth" priority />
        </div>
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Secure login</p>
        <h1 className="text-3xl font-black tracking-normal">Verify login OTP</h1>
        <p className="mt-3 text-sm font-medium leading-6 text-[#6b767d]">OTP expires in 10 minutes.</p>
        <div className="mt-6 grid gap-4">
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input id="email" className="field" readOnly value={pending.email} />
          </div>
          <div>
            <label className="label" htmlFor="otp">
              6-digit OTP
            </label>
            <input id="otp" className="field" inputMode="numeric" maxLength={6} minLength={6} required value={otp} onChange={(event) => setOtp(event.target.value)} />
          </div>
          <label className="flex items-start gap-3 rounded-lg border border-black/10 bg-white/70 p-3 text-sm font-bold text-[#526069]">
            <input className="mt-1 h-4 w-4 accent-teal-600" type="checkbox" checked={rememberDevice} onChange={(event) => setRememberDevice(event.target.checked)} />
            <span>Remember this device for future secure logins.</span>
          </label>
          <button className="btn-primary" disabled={loading} type="submit">
            {loading && <Loader2 className="animate-spin" size={18} />}
            Verify and continue
          </button>
          <button className="btn-secondary" disabled={resending || cooldown > 0 || !pending.login_challenge_id} onClick={resend} type="button">
            {resending && <Loader2 className="animate-spin" size={18} />}
            {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend OTP"}
          </button>
        </div>
      </form>
    </main>
  );
}
