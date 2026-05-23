"use client";

import { Building2, Globe2, Loader2, MapPin, Send, Star, UsersRound } from "lucide-react";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import BlueTick from "@/components/BlueTick";
import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl, getStoredUser } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Application, CompanyDetail, CompanyReview, User } from "@/types";

export default function CompanyDetailPage() {
  const params = useParams<{ id: string }>();
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [reviews, setReviews] = useState<CompanyReview[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ rating: 5, review_text: "" });

  const load = () => {
    if (!params.id) return;
    Promise.all([apiFetch<CompanyDetail>(`/companies/${params.id}`), apiFetch<CompanyReview[]>(`/companies/${params.id}/reviews`)])
      .then(([companyData, reviewRows]) => {
        setCompany(companyData);
        setReviews(reviewRows);
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Company failed"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    setUser(getStoredUser());
    load();
  }, [params.id]);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored?.role !== "JOB_SEEKER") return;
    apiFetch<Application[]>("/applications/my").then(setApplications).catch(() => setApplications([]));
  }, []);

  const canReview = useMemo(() => {
    if (!company || user?.role !== "JOB_SEEKER") return false;
    return applications.some((application) => application.job?.company_id === company.id);
  }, [applications, company, user?.role]);

  const alreadyReviewed = useMemo(() => {
    if (!user) return false;
    return reviews.some((review) => review.job_seeker_id === user.id);
  }, [reviews, user]);

  const submitReview = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!company) return;
    setSaving(true);
    try {
      await apiFetch<CompanyReview>(`/companies/${company.id}/reviews`, {
        method: "POST",
        body: JSON.stringify({ rating: form.rating, review_text: form.review_text || null })
      });
      toast.success("Review submitted");
      setForm({ rating: 5, review_text: "" });
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Review failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <main className="page-shell">Loading company...</main>;
  if (!company) return <main className="page-shell"><EmptyState title="Company unavailable" text="This company profile could not be found." /></main>;

  return (
    <main className="page-shell">
      <PageHeader title={company.company_name} eyebrow={company.industry || company.company_type}>
        <VerificationStatusBadge status={company.verification_status} />
      </PageHeader>

      <section className="grid gap-5 lg:grid-cols-[360px_1fr]">
        <aside className="panel p-5">
          <div className="grid h-32 w-32 place-items-center overflow-hidden rounded-lg border border-black/10 bg-white">
            {company.company_logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={assetUrl(company.company_logo_url)} alt={company.company_name} className="h-full w-full object-cover" />
            ) : (
              <Building2 size={34} />
            )}
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <h2 className="text-2xl font-black">{company.company_name}</h2>
            {company.verification_status === "VERIFIED" && <BlueTick label="Verified Company" />}
          </div>
          <div className="mt-4 grid gap-3 text-sm font-bold text-[#526069]">
            <span className="flex items-center gap-2"><MapPin size={16} /> {company.headquarters_location || "Location not added"}</span>
            {company.website && <a className="flex items-center gap-2 text-teal-700" href={company.website} target="_blank" rel="noreferrer"><Globe2 size={16} /> Website</a>}
            <span className="flex items-center gap-2"><UsersRound size={16} /> {company.recruiter_count} recruiters</span>
            <span className="flex items-center gap-2"><Star size={16} /> {company.average_rating.toFixed(1)} from {company.total_reviews} reviews</span>
          </div>
          <p className="mt-5 text-sm font-medium leading-6 text-[#526069]">{company.description || "No company description added yet."}</p>
        </aside>

        <div className="grid gap-5">
          <section className="panel p-5">
            <h2 className="text-xl font-black">Active jobs</h2>
            {company.active_jobs.length === 0 ? (
              <p className="mt-3 text-sm font-bold text-[#6b767d]">No active public jobs right now.</p>
            ) : (
              <div className="mt-4 grid gap-4">
                {company.active_jobs.map((job) => (
                  <JobCard key={job.id} job={job} detailsHref={`/jobseeker/jobs/${job.id}`} />
                ))}
              </div>
            )}
          </section>

          <section className="panel p-5">
            <h2 className="text-xl font-black">Recruiters</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {company.recruiters.map((recruiter) => (
                <div key={recruiter.id} className="rounded-lg border border-black/10 bg-white/70 p-4">
                  <p className="font-black text-[#172026]">{recruiter.recruiter_name}</p>
                  <p className="text-sm font-bold text-[#6b767d]">{recruiter.designation || "Recruiter"}{recruiter.department ? `, ${recruiter.department}` : ""}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <VerificationStatusBadge status={recruiter.recruiter_verification_status} />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel p-5">
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
              <h2 className="text-xl font-black">Reviews</h2>
              <span className="text-sm font-black text-amber-700">{company.average_rating.toFixed(1)} / 5</span>
            </div>
            <div className="mt-4 grid gap-3">
              {reviews.length === 0 ? (
                <p className="text-sm font-bold text-[#6b767d]">No visible reviews yet.</p>
              ) : (
                reviews.map((review) => (
                  <div key={review.id} className="rounded-lg border border-black/10 bg-white/70 p-4">
                    <div className="flex flex-wrap justify-between gap-2">
                      <p className="font-black text-[#172026]">{review.reviewer_name || "Job seeker"}</p>
                      <span className="font-black text-amber-700">{review.rating} / 5</span>
                    </div>
                    {review.review_text && <p className="mt-2 text-sm font-medium leading-6 text-[#526069]">{review.review_text}</p>}
                    <p className="mt-2 text-xs font-bold text-[#8a949a]">{formatDate(review.created_at)}</p>
                  </div>
                ))
              )}
            </div>

            {user?.role === "JOB_SEEKER" && canReview && !alreadyReviewed && (
              <form onSubmit={submitReview} className="mt-5 grid gap-3 rounded-lg border border-black/10 bg-[#fbfaf7] p-4">
                <select className="field" value={form.rating} onChange={(event) => setForm({ ...form, rating: Number(event.target.value) })}>
                  {[5, 4, 3, 2, 1].map((rating) => (
                    <option key={rating} value={rating}>{rating} star{rating === 1 ? "" : "s"}</option>
                  ))}
                </select>
                <textarea className="field min-h-28" placeholder="Share your experience" value={form.review_text} onChange={(event) => setForm({ ...form, review_text: event.target.value })} />
                <button className="btn-primary" type="submit" disabled={saving}>
                  {saving ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                  Write Review
                </button>
              </form>
            )}
            {user?.role === "JOB_SEEKER" && !canReview && (
              <p className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                You can review this company after applying to one of its jobs.
              </p>
            )}
            {user?.role === "JOB_SEEKER" && alreadyReviewed && (
              <p className="mt-5 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-bold text-emerald-700">
                You have already reviewed this company.
              </p>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}
