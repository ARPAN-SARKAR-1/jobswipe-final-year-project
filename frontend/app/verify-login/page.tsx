"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";

import { apiFetch, roleHome, saveAuth } from "@/lib/api";
import type { AuthResponse } from "@/types";

type PendingLogin = {
  email: string;
  login_challenge_id: string;
};

export default function VerifyLoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<PendingLogin>({ email: "", login_challenge_id: "" });
  const [otp, setOtp] = useState("");
  const [rememberDevice, setRememberDevice] = useState(false);

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
      router.push(roleHome(auth.user!.role));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel mx-auto max-w-md p-6 md:p-8">
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Secure login</p>
        <h1 className="text-3xl font-black tracking-normal">Verify login OTP</h1>
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
        </div>
      </form>
    </main>
  );
}
