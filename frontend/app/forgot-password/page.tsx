"use client";

import { Loader2 } from "lucide-react";
import { FormEvent, useState } from "react";
import toast from "react-hot-toast";

import CaptchaBox, { type CaptchaValue } from "@/components/CaptchaBox";
import { apiFetch } from "@/lib/api";

type ForgotResponse = {
  message: string;
};

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<ForgotResponse | null>(null);
  const [captcha, setCaptcha] = useState<CaptchaValue>({ captcha_id: "", captcha_answer: "" });
  const [captchaRefresh, setCaptchaRefresh] = useState(0);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    try {
      const data = await apiFetch<ForgotResponse>("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email, ...captcha })
      });
      setResponse(data);
      toast.success("Password reset instructions generated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Request failed");
      setCaptchaRefresh((value) => value + 1);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <form onSubmit={submit} className="panel mx-auto max-w-md p-6 md:p-8">
        <p className="mb-2 text-sm font-black uppercase text-teal-700">Password help</p>
        <h1 className="text-3xl font-black tracking-normal">Forgot password</h1>
        <p className="mt-3 text-sm font-medium leading-6 text-[#6b767d]">Enter your email. If the account exists, reset instructions will be generated.</p>
        <div className="mt-6 grid gap-4">
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input id="email" className="field" required type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <CaptchaBox value={captcha} onChange={setCaptcha} refreshSignal={captchaRefresh} />
          <button className="btn-primary" disabled={loading} type="submit">
            {loading && <Loader2 className="animate-spin" size={18} />}
            Request reset instructions
          </button>
        </div>
        {response && (
          <div className="mt-5 rounded-lg border border-teal-200 bg-teal-50 p-4 text-sm font-bold text-teal-800">
            <p>{response.message}</p>
          </div>
        )}
      </form>
    </main>
  );
}
