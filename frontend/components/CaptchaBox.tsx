"use client";

import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";

type CaptchaChallenge = {
  challenge_id: string;
  image_base64: string;
  purpose: string;
  expires_at: string;
  expires_in_seconds: number;
};

export type CaptchaValue = {
  challengeId: string;
  answer: string;
};

type CaptchaBoxProps = {
  disabled?: boolean;
  onChange: (value: CaptchaValue) => void;
  purpose: "login" | "signup" | "forgot_password" | "report";
};

export default function CaptchaBox({ disabled = false, onChange, purpose }: CaptchaBoxProps) {
  const [challenge, setChallenge] = useState<CaptchaChallenge | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadChallenge = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<CaptchaChallenge>(`/auth/captcha?purpose=${encodeURIComponent(purpose)}`);
      setChallenge(data);
      setAnswer("");
      onChange({ challengeId: data.challenge_id, answer: "" });
    } catch (loadError) {
      console.error("CAPTCHA challenge fetch failed", {
        purpose,
        message: loadError instanceof Error ? loadError.message : "Unknown error"
      });
      setChallenge(null);
      setError("Security check could not load. Please refresh or try again.");
      onChange({ challengeId: "", answer: "" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadChallenge();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [purpose]);

  const updateAnswer = (value: string) => {
    setAnswer(value);
    onChange({ challengeId: challenge?.challenge_id ?? "", answer: value });
  };

  return (
    <div className="rounded-lg border border-black/10 bg-white/70 p-3">
      <div className="mb-2 flex items-center justify-between gap-3">
        <label className="label !mb-0" htmlFor={`${purpose}-captcha`}>
          Security check
        </label>
        <button className="btn-secondary !px-2 !py-2" disabled={disabled || loading} onClick={loadChallenge} title="Refresh security check" type="button">
          <RefreshCw className={loading ? "animate-spin" : ""} size={16} />
        </button>
      </div>
      {error ? (
        <p className="text-sm font-bold text-rose-700">{error}</p>
      ) : challenge?.image_base64 ? (
        <div className="mb-3 rounded-lg border border-black/10 bg-[#fbfaf7] p-2">
          <img alt="Security check image" className="h-20 w-full object-contain" draggable={false} src={challenge.image_base64} />
        </div>
      ) : (
        <p className="mb-3 text-sm font-bold text-[#526069]">Connecting to the server. This may take a few seconds.</p>
      )}
      <label className="label" htmlFor={`${purpose}-captcha`}>
        Solve the security puzzle to continue
      </label>
      <input
        id={`${purpose}-captcha`}
        className="field"
        disabled={disabled || loading || !challenge}
        inputMode="numeric"
        required
        value={answer}
        onChange={(event) => updateAnswer(event.target.value)}
      />
    </div>
  );
}
