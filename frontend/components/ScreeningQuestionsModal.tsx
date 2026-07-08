"use client";

import { Loader2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type ScreeningJob = {
  title?: string | null;
  screening_questions?: string[] | null;
};

export function getScreeningQuestions(job?: ScreeningJob | null) {
  return Array.isArray(job?.screening_questions)
    ? job.screening_questions.map((question) => question.trim()).filter(Boolean).slice(0, 5)
    : [];
}

export default function ScreeningQuestionsModal({
  job,
  open,
  submitting,
  onCancel,
  onSubmit
}: {
  job: ScreeningJob | null;
  open: boolean;
  submitting?: boolean;
  onCancel: () => void;
  onSubmit: (answers: string[]) => void;
}) {
  const questions = useMemo(() => getScreeningQuestions(job), [job]);
  const [answers, setAnswers] = useState<string[]>([]);

  useEffect(() => {
    if (open) setAnswers(questions.map(() => ""));
  }, [open, questions.length]);

  if (!open || questions.length === 0) return null;

  const canSubmit = answers.length === questions.length && answers.every((answer) => answer.trim().length > 0);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/35 p-4">
      <form
        className="w-full max-w-xl rounded-lg bg-white p-4 shadow-premium sm:p-5"
        onSubmit={(event) => {
          event.preventDefault();
          if (canSubmit) onSubmit(answers.map((answer) => answer.trim()));
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase text-teal-700">Screening questions</p>
            <h2 className="mt-1 text-xl font-black text-[#172026]">Answer before applying</h2>
            {job?.title && <p className="mt-1 text-sm font-bold text-[#6b767d]">{job.title}</p>}
          </div>
          <button className="btn-secondary !px-3 !py-2" type="button" aria-label="Close screening questions" onClick={onCancel}>
            <X size={16} />
          </button>
        </div>

        <div className="mt-5 grid max-h-[60vh] gap-4 overflow-y-auto pr-1">
          {questions.map((question, index) => (
            <label key={`${question}-${index}`} className="grid gap-2">
              <span className="text-sm font-black text-[#172026]">{question}</span>
              <textarea
                className="field min-h-24"
                maxLength={1200}
                required
                value={answers[index] || ""}
                onChange={(event) => {
                  const next = [...answers];
                  next[index] = event.target.value;
                  setAnswers(next);
                }}
                placeholder="Write your answer"
              />
            </label>
          ))}
        </div>

        <p className="mt-4 rounded-lg bg-teal-50 p-3 text-xs font-bold leading-5 text-teal-800">
          Your answers are shared only with the recruiter for this application.
        </p>

        <div className="mt-5 grid gap-2 sm:grid-cols-2">
          <button className="btn-secondary" type="button" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn-primary" type="submit" disabled={!canSubmit || submitting}>
            {submitting && <Loader2 className="animate-spin" size={17} />}
            Submit application
          </button>
        </div>
      </form>
    </div>
  );
}
