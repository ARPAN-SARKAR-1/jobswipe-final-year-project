"use client";

import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";

export type CaptchaValue = {
  captcha_id: string;
  captcha_answer: string;
};

type CaptchaChallenge = {
  captcha_id: string;
  question: string;
};

type CaptchaBoxProps = {
  value: CaptchaValue;
  onChange: (value: CaptchaValue) => void;
  refreshSignal?: number;
};

export default function CaptchaBox({ value, onChange, refreshSignal = 0 }: CaptchaBoxProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  const loadCaptcha = async () => {
    setLoading(true);
    try {
      const challenge = await apiFetch<CaptchaChallenge>("/security/captcha");
      setQuestion(challenge.question);
      onChange({ captcha_id: challenge.captcha_id, captcha_answer: "" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCaptcha().catch(() => setQuestion("CAPTCHA unavailable"));
  }, [refreshSignal]);

  return (
    <div className="rounded-lg border border-black/10 bg-white/80 p-3">
      <div className="flex items-center justify-between gap-3">
        <label className="label mb-0" htmlFor="captcha_answer">
          CAPTCHA
        </label>
        <button className="rounded-md border border-black/10 p-2 text-[#526069] hover:border-teal-400 hover:text-teal-700" type="button" onClick={loadCaptcha} disabled={loading} title="Refresh CAPTCHA">
          <RefreshCw className={loading ? "animate-spin" : ""} size={16} />
        </button>
      </div>
      <p className="mt-2 text-sm font-black text-[#263238]">{question || "Loading challenge..."}</p>
      <input
        id="captcha_answer"
        className="field mt-3"
        required
        inputMode="numeric"
        value={value.captcha_answer}
        onChange={(event) => onChange({ ...value, captcha_answer: event.target.value })}
        placeholder="Answer"
      />
    </div>
  );
}
