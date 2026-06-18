"use client";

import { Building2, Star } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useParams } from "next/navigation";

import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import TrustBadge from "@/components/TrustBadge";
import { apiFetch, assetUrl, getStoredUser } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { CompanyPublicProfile } from "@/types";

const initialReview = { rating: 5, title: "", review_text: "" };

export default function PublicCompanyPage() {
  const params = useParams<{ id: string }>();
  const [company, setCompany] = useState<CompanyPublicProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewForm, setReviewForm] = useState(initialReview);
  const user = getStoredUser();

  const load = () => {
    if (!params.id) return;
    setLoading(true);
    apiFetch<CompanyPublicProfile>(`/companies/${params.id}`)
      .then(setCompany)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Company failed to load"))
      .finally(() => setLoading(false));
  };

  useEffect(load, [params.id]);

  const submitReview = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!company) return;
    try {
      await apiFetch(`/companies/${company.id}/reviews`, {
        method: "POST",
        body: JSON.stringify(reviewForm)
      });
      toast.success("Review submitted");
      setReviewForm(initialReview);
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Review failed");
    }
  };

  if (loading) return <main className="page-shell">Loading company...</main>;
  if (!company) return <main className="page-shell"><EmptyState title="Company unavailable" text="This company profile could not be loaded." /></main>;

  const logo = assetUrl(company.company_logo_url);

  return (
    <main className="page-shell">
      <PageHeader title={company.company_name || "Company Profile"} eyebrow="Company trust" />
      <section className="panel p-5">
        <div className="flex flex-col gap-5 md:flex-row md:items-start">
          <div className="grid h-24 w-24 shrink-0 place-items-center overflow-hidden rounded-lg border border-black/10 bg-white">
            {logo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={logo} alt={company.company_name || "Company"} className="h-full w-full object-cover" />
            ) : (
              <Building2 size={28} />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-black">{company.company_name || "Company"}</h1>
              <TrustBadge label="Verified company" verified={company.verification_status === "VERIFIED"} />
            </div>
            <p className="mt-2 text-sm font-bold text-[#6b767d]">
              {[company.company_type, company.industry, company.company_size, company.headquarters || company.location].filter(Boolean).join(" / ")}
            </p>
            <div className="mt-2 flex flex-wrap gap-3">
              {company.website && <a className="text-sm font-black text-teal-700" href={company.website} target="_blank" rel="noreferrer">Visit website</a>}
              {company.career_page_url && <a className="text-sm font-black text-teal-700" href={company.career_page_url} target="_blank" rel="noreferrer">Career page</a>}
              {company.linkedin_url && <a className="text-sm font-black text-teal-700" href={company.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</a>}
            </div>
            {company.verification_status !== "VERIFIED" && (
              <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                This company has not been verified by Swipe for Success yet.
              </p>
            )}
            {(company.about_company || company.description) && <p className="mt-4 max-w-3xl text-sm font-medium leading-6 text-[#526069]">{company.about_company || company.description}</p>}
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="rounded-lg bg-amber-50 px-2.5 py-1 text-xs font-black text-amber-800">
                {company.average_rating ? `${company.average_rating}/5` : "No rating yet"}
              </span>
              <span className="rounded-lg bg-white px-2.5 py-1 text-xs font-black text-[#526069]">{company.review_count} reviews</span>
              <span className="rounded-lg bg-white px-2.5 py-1 text-xs font-black text-[#526069]">{company.verified_recruiter_count} verified recruiters</span>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="grid gap-4">
          <section className="panel grid gap-4 p-5 md:grid-cols-2">
            <InfoBlock title="Company size" value={company.company_size || (company.employee_count_estimate ? `${company.employee_count_estimate} employees` : null)} />
            <InfoBlock title="Headquarters" value={company.headquarters || company.location} />
            <InfoBlock title="Founded" value={company.founded_year ? String(company.founded_year) : null} />
            <InfoBlock title="Work mode" value={company.work_mode} />
            <InfoBlock title="Culture" value={company.culture_summary} wide />
            <InfoBlock title="Benefits" value={company.benefits} wide />
            <InfoBlock title="Hiring process" value={company.hiring_process} wide />
          </section>

          {(company.glassdoor_url || company.ambitionbox_url) && (
            <section className="panel p-5">
              <h2 className="text-xl font-black">External references</h2>
              <p className="mt-2 text-sm font-bold text-[#6b767d]">These links are external references only. Swipe for Success does not import or copy third-party reviews.</p>
              <div className="mt-3 flex flex-wrap gap-3">
                {company.glassdoor_url && <a className="text-sm font-black text-teal-700" href={company.glassdoor_url} target="_blank" rel="noreferrer">Glassdoor</a>}
                {company.ambitionbox_url && <a className="text-sm font-black text-teal-700" href={company.ambitionbox_url} target="_blank" rel="noreferrer">AmbitionBox</a>}
              </div>
            </section>
          )}

          <h2 className="text-xl font-black">Active Jobs</h2>
          {company.active_jobs.length === 0 ? (
            <EmptyState title="No active jobs" text="Verified jobs from this company will appear here." />
          ) : (
            company.active_jobs.map((job) => <JobCard key={job.id} job={job} detailsHref={`/jobseeker/jobs/${job.id}`} />)
          )}
        </div>

        <aside className="grid gap-4">
          <div className="panel p-5">
            <h2 className="text-xl font-black">Company-provided testimonials</h2>
            <div className="mt-4 grid gap-3">
              {!company.company_testimonials || company.company_testimonials.length === 0 ? (
                <p className="text-sm font-bold text-[#6b767d]">No approved company-provided testimonials yet.</p>
              ) : (
                company.company_testimonials.map((item) => (
                  <div key={item.id} className="rounded-lg border border-black/10 bg-white/70 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-black text-[#172026]">{item.title}</p>
                      {item.rating && <span className="inline-flex items-center gap-1 text-xs font-black text-amber-700"><Star size={13} /> {item.rating}</span>}
                    </div>
                    <p className="mt-1 text-xs font-black text-teal-700">Company-provided testimonial</p>
                    {item.reviewer_label && <p className="mt-1 text-xs font-bold text-[#8a949a]">{item.reviewer_label}</p>}
                    <p className="mt-2 text-sm font-medium leading-6 text-[#526069]">{item.statement}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="panel p-5">
            <h2 className="text-xl font-black">Reviews</h2>
            <div className="mt-4 grid gap-3">
              {company.visible_reviews.length === 0 ? (
                <p className="text-sm font-bold text-[#6b767d]">No visible reviews yet.</p>
              ) : (
                company.visible_reviews.map((review) => (
                  <div key={review.id} className="rounded-lg border border-black/10 bg-white/70 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-black text-[#172026]">{review.title}</p>
                      <span className="inline-flex items-center gap-1 text-xs font-black text-amber-700"><Star size={13} /> {review.rating}</span>
                    </div>
                    <p className="mt-1 text-xs font-bold text-[#8a949a]">{review.reviewer_name || "Job seeker"} / {formatDate(review.created_at)}</p>
                    <p className="mt-2 text-sm font-medium leading-6 text-[#526069]">{review.review_text}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          {user?.role === "JOB_SEEKER" && (
            <form onSubmit={submitReview} className="panel grid gap-3 p-5">
              <h2 className="text-xl font-black">Write Review</h2>
              <select className="field" value={reviewForm.rating} onChange={(event) => setReviewForm({ ...reviewForm, rating: Number(event.target.value) })}>
                {[5, 4, 3, 2, 1].map((rating) => (
                  <option key={rating} value={rating}>{rating} stars</option>
                ))}
              </select>
              <input className="field" required minLength={3} placeholder="Review title" value={reviewForm.title} onChange={(event) => setReviewForm({ ...reviewForm, title: event.target.value })} />
              <textarea className="field min-h-28" required minLength={10} placeholder="Share your experience" value={reviewForm.review_text} onChange={(event) => setReviewForm({ ...reviewForm, review_text: event.target.value })} />
              <button className="btn-primary" type="submit">Submit review</button>
            </form>
          )}
        </aside>
      </section>
    </main>
  );
}

function InfoBlock({ title, value, wide }: { title: string; value?: string | null; wide?: boolean }) {
  if (!value) return null;
  return (
    <div className={wide ? "md:col-span-2" : ""}>
      <p className="text-xs font-black uppercase tracking-wide text-[#8a949a]">{title}</p>
      <p className="mt-1 whitespace-pre-line text-sm font-bold leading-6 text-[#526069]">{value}</p>
    </div>
  );
}
