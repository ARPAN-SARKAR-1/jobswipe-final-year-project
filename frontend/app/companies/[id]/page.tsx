"use client";

import { Building2, Globe2, MapPin, Star, UsersRound } from "lucide-react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import BlueTick from "@/components/BlueTick";
import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import RatingSummary from "@/components/RatingSummary";
import ReviewCard from "@/components/ReviewCard";
import ReviewFormModal, { type CompanyReviewPayload } from "@/components/ReviewFormModal";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl, getStoredUser } from "@/lib/api";
import type { Application, CompanyDetail, CompanyReview, CompanyReviewSummary, User } from "@/types";

const REVIEW_ELIGIBLE_APPLICATION_STATUSES = new Set<Application["status"]>(["SHORTLISTED"]);

export default function CompanyDetailPage() {
  const params = useParams<{ id: string }>();
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [reviews, setReviews] = useState<CompanyReview[]>([]);
  const [summary, setSummary] = useState<CompanyReviewSummary | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);

  const load = () => {
    if (!params.id) return;
    Promise.all([
      apiFetch<CompanyDetail>(`/companies/${params.id}`),
      apiFetch<CompanyReview[]>(`/companies/${params.id}/reviews`),
      apiFetch<CompanyReviewSummary>(`/companies/${params.id}/review-summary`)
    ])
      .then(([companyData, reviewRows, summaryData]) => {
        setCompany(companyData);
        setReviews(reviewRows);
        setSummary(summaryData);
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
    return applications.some(
      (application) =>
        application.job?.company_id === company.id &&
        REVIEW_ELIGIBLE_APPLICATION_STATUSES.has(application.status)
    );
  }, [applications, company, user?.role]);

  const alreadyReviewed = useMemo(() => {
    if (!user) return false;
    return reviews.some((review) => review.job_seeker_id === user.id);
  }, [reviews, user]);

  const submitReview = async (payload: CompanyReviewPayload) => {
    if (!company) return;
    setSaving(true);
    try {
      await apiFetch<CompanyReview>(`/companies/${company.id}/reviews`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      toast.success("Review submitted");
      setReviewOpen(false);
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
          {summary && (
            <RatingSummary
              title="Company Rating"
              average={summary.average_overall_rating}
              total={summary.total_reviews}
              rows={[
                { label: "Work Culture", value: summary.work_culture_average },
                { label: "Interview Process", value: summary.interview_process_average },
                { label: "Salary Transparency", value: summary.salary_transparency_average },
                { label: "Growth Opportunity", value: summary.growth_opportunity_average }
              ]}
            />
          )}

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
                  <Link href={`/recruiters/${recruiter.user_id}`} className="font-black text-[#172026] hover:text-teal-700">
                    {recruiter.recruiter_name}
                  </Link>
                  <p className="text-sm font-bold text-[#6b767d]">{recruiter.designation || "Recruiter"}{recruiter.department ? `, ${recruiter.department}` : ""}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <VerificationStatusBadge status={recruiter.recruiter_verification_status} />
                    <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-black text-amber-700">
                      {recruiter.average_rating.toFixed(1)} ({recruiter.total_reviews})
                    </span>
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
                  <ReviewCard
                    key={review.id}
                    reviewerName={review.reviewer_name}
                    title={review.review_title}
                    text={review.review_text}
                    rating={review.overall_rating}
                    pros={review.pros}
                    cons={review.cons}
                    createdAt={review.created_at}
                    badges={[
                      `Culture ${review.work_culture_rating}`,
                      `Interview ${review.interview_process_rating}`,
                      `Salary ${review.salary_transparency_rating}`,
                      `Growth ${review.growth_opportunity_rating}`
                    ]}
                  />
                ))
              )}
            </div>

            {user?.role === "JOB_SEEKER" && canReview && !alreadyReviewed && (
              <button className="btn-primary mt-5" type="button" onClick={() => setReviewOpen(true)}>
                Write Review
              </button>
            )}
            {user?.role === "JOB_SEEKER" && !canReview && (
              <p className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                You can review this company only after being shortlisted or selected.
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
      <ReviewFormModal
        open={reviewOpen}
        mode="company"
        title={`Review ${company.company_name}`}
        saving={saving}
        onClose={() => setReviewOpen(false)}
        onSubmit={(payload) => submitReview(payload as CompanyReviewPayload)}
      />
    </main>
  );
}
