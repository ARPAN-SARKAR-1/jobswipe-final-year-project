"use client";

import { Loader2, Send, X } from "lucide-react";
import { FormEvent, useState } from "react";

import RatingStars from "@/components/RatingStars";

export type CompanyReviewPayload = {
  overall_rating: number;
  work_culture_rating: number;
  interview_process_rating: number;
  salary_transparency_rating: number;
  growth_opportunity_rating: number;
  review_title?: string | null;
  review_text?: string | null;
  pros?: string | null;
  cons?: string | null;
  is_anonymous: boolean;
};

export type RecruiterReviewPayload = {
  overall_rating: number;
  communication_rating: number;
  response_time_rating: number;
  professionalism_rating: number;
  transparency_rating: number;
  review_title?: string | null;
  review_text?: string | null;
  is_anonymous: boolean;
};

type ReviewFormModalProps = {
  open: boolean;
  mode: "company" | "recruiter";
  title: string;
  saving: boolean;
  onClose: () => void;
  onSubmit: (payload: CompanyReviewPayload | RecruiterReviewPayload) => Promise<void>;
};

const baseCompany: CompanyReviewPayload = {
  overall_rating: 5,
  work_culture_rating: 5,
  interview_process_rating: 5,
  salary_transparency_rating: 5,
  growth_opportunity_rating: 5,
  review_title: "",
  review_text: "",
  pros: "",
  cons: "",
  is_anonymous: false
};

const baseRecruiter: RecruiterReviewPayload = {
  overall_rating: 5,
  communication_rating: 5,
  response_time_rating: 5,
  professionalism_rating: 5,
  transparency_rating: 5,
  review_title: "",
  review_text: "",
  is_anonymous: false
};

function cleanPayload<T extends Record<string, unknown>>(payload: T): T {
  return Object.fromEntries(Object.entries(payload).map(([key, value]) => [key, typeof value === "string" ? value.trim() || null : value])) as T;
}

export default function ReviewFormModal({ open, mode, title, saving, onClose, onSubmit }: ReviewFormModalProps) {
  const [companyForm, setCompanyForm] = useState<CompanyReviewPayload>(baseCompany);
  const [recruiterForm, setRecruiterForm] = useState<RecruiterReviewPayload>(baseRecruiter);

  if (!open) return null;

  const isCompany = mode === "company";
  const form = isCompany ? companyForm : recruiterForm;
  const setRating = (key: string, value: number) => {
    if (isCompany) setCompanyForm((current) => ({ ...current, [key]: value }));
    else setRecruiterForm((current) => ({ ...current, [key]: value }));
  };
  const setField = (key: string, value: string | boolean) => {
    if (isCompany) setCompanyForm((current) => ({ ...current, [key]: value }));
    else setRecruiterForm((current) => ({ ...current, [key]: value }));
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit(cleanPayload(form));
    setCompanyForm(baseCompany);
    setRecruiterForm(baseRecruiter);
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
      <form onSubmit={submit} className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-[#f7f3ea] p-5 shadow-2xl">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-xl font-black text-[#172026]">{title}</h2>
          <button className="btn-secondary !p-2" type="button" onClick={onClose} aria-label="Close review form">
            <X size={18} />
          </button>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2">
          <RatingStars value={form.overall_rating} onChange={(value) => setRating("overall_rating", value)} label="Overall" />
          {isCompany ? (
            <>
              <RatingStars value={(form as CompanyReviewPayload).work_culture_rating} onChange={(value) => setRating("work_culture_rating", value)} label="Work Culture" />
              <RatingStars value={(form as CompanyReviewPayload).interview_process_rating} onChange={(value) => setRating("interview_process_rating", value)} label="Interview Process" />
              <RatingStars value={(form as CompanyReviewPayload).salary_transparency_rating} onChange={(value) => setRating("salary_transparency_rating", value)} label="Salary Transparency" />
              <RatingStars value={(form as CompanyReviewPayload).growth_opportunity_rating} onChange={(value) => setRating("growth_opportunity_rating", value)} label="Growth Opportunity" />
            </>
          ) : (
            <>
              <RatingStars value={(form as RecruiterReviewPayload).communication_rating} onChange={(value) => setRating("communication_rating", value)} label="Communication" />
              <RatingStars value={(form as RecruiterReviewPayload).response_time_rating} onChange={(value) => setRating("response_time_rating", value)} label="Response Time" />
              <RatingStars value={(form as RecruiterReviewPayload).professionalism_rating} onChange={(value) => setRating("professionalism_rating", value)} label="Professionalism" />
              <RatingStars value={(form as RecruiterReviewPayload).transparency_rating} onChange={(value) => setRating("transparency_rating", value)} label="Transparency" />
            </>
          )}
        </div>

        <div className="mt-5 grid gap-3">
          <input className="field" maxLength={160} placeholder="Review title" value={form.review_title || ""} onChange={(event) => setField("review_title", event.target.value)} />
          <textarea className="field min-h-28" maxLength={3000} placeholder="Share your experience" value={form.review_text || ""} onChange={(event) => setField("review_text", event.target.value)} />
          {isCompany && (
            <div className="grid gap-3 md:grid-cols-2">
              <textarea className="field min-h-24" maxLength={1500} placeholder="Pros" value={(form as CompanyReviewPayload).pros || ""} onChange={(event) => setField("pros", event.target.value)} />
              <textarea className="field min-h-24" maxLength={1500} placeholder="Cons" value={(form as CompanyReviewPayload).cons || ""} onChange={(event) => setField("cons", event.target.value)} />
            </div>
          )}
          <label className="flex items-center gap-2 text-sm font-bold text-[#526069]">
            <input type="checkbox" checked={form.is_anonymous} onChange={(event) => setField("is_anonymous", event.target.checked)} />
            Post anonymously
          </label>
          <div className="flex justify-end gap-3">
            <button className="btn-secondary" type="button" onClick={onClose}>
              Cancel
            </button>
            <button className="btn-primary" type="submit" disabled={saving}>
              {saving ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
              Submit Review
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
