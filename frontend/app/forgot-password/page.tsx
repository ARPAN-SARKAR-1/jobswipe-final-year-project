"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";
import toast from "react-hot-toast";

import { apiFetch } from "@/lib/api";

type ForgotResponse = {
  message: string;
  reset_token?: string | null;
  reset_url?: string | null;
};

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<ForgotResponse | null>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    try {
      const data = await apiFetch<ForgotResponse>("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email })
      });
      setResponse(data);
      toast.success("Reset token generated for demo");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel mx-auto max-w-md p-6 md:p-8">
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Password help</p>
        <h1 className="text-3xl font-black tracking-normal">Forgot password</h1>
        <p className="mt-3 text-sm font-medium leading-6 text-[#6b767d]">Enter your email. In development mode, JobSwipe returns a reset token for demo.</p>
        <div className="mt-6 grid gap-4">
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input id="email" className="field" required type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <button className="btn-primary" disabled={loading} type="submit">
            {loading && <Loader2 className="animate-spin" size={18} />}
            Generate reset token
          </button>
        </div>
        {response?.reset_token && (
          <div className="mt-5 rounded-lg border border-teal-200 bg-teal-50 p-4 text-sm font-bold text-teal-800">
            <p className="break-all">Token: {response.reset_token}</p>
            {response.reset_url && (
              <Link href={response.reset_url.replace(/^.*\/reset-password/, "/reset-password")} className="mt-3 inline-block underline">
                Open reset page
              </Link>
            )}
          </div>
        )}
      </form>
    </main>
  );
}
