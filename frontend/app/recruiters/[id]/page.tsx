"use client";

import { Building2, BriefcaseBusiness, MessageCircle, Star } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import BlueTick from "@/components/BlueTick";
import EmptyState from "@/components/EmptyState";
import JobCard from "@/components/JobCard";
import PageHeader from "@/components/PageHeader";
import RatingSummary from "@/components/RatingSummary";
import ReviewCard from "@/components/ReviewCard";
import ReviewFormModal, { type RecruiterReviewPayload } from "@/components/ReviewFormModal";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl, getStoredUser } from "@/lib/api";
import type { Application, Job, RecruiterPublicProfile, RecruiterReview, RecruiterReviewSummary, User } from "@/types";

const REVIEW_ELIGIBLE_APPLICATION_STATUSES = new Set<Application["status"]>(["SHORTLISTED"]);

export default function RecruiterProfilePage() {
  const params = useParams<{ id: string }>();
  const [profile, setProfile] = useState<RecruiterPublicProfile | null>(null);
  const [summary, setSummary] = useState<RecruiterReviewSummary | null>(null);
  const [reviews, setReviews] = useState<RecruiterReview[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!params.id) return;
    Promise.all([
      apiFetch<RecruiterPublicProfile>(`/recruiters/${params.id}`),
      apiFetch<RecruiterReviewSummary>(`/recruiters/${params.id}/review-summary`),
      apiFetch<RecruiterReview[]>(`/recruiters/${params.id}/reviews`),
      apiFetch<Job[]>(`/recruiters/${params.id}/jobs`)
    ])
      .then(([profileData, summaryData, reviewRows, jobRows]) => {
        setProfile(profileData);
        setSummary(summaryData);
        setReviews(reviewRows);
        setJobs(jobRows);
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Recruiter profile failed"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const stored = getStoredUser();
    setUser(stored);
    load();
    if (stored?.role === "JOB_SEEKER") {
      apiFetch<Application[]>("/applications/my").then(setApplications).catch(() => setApplications([]));
    }
  }, [params.id]);

  const canReview = useMemo(() => {
    if (!profile || user?.role !== "JOB_SEEKER") return false;
    return applications.some(
      (application) =>
        application.job?.recruiter_id === profile.id &&
        REVIEW_ELIGIBLE_APPLICATION_STATUSES.has(application.status)
    );
  }, [applications, profile, user?.role]);

  const alreadyReviewed = useMemo(() => {
    if (!user) return false;
    return reviews.some((review) => review.job_seeker_id === user.id);
  }, [reviews, user]);

  const submitReview = async (payload: RecruiterReviewPayload) => {
    if (!profile) return;
    setSaving(true);
    try {
      await apiFetch<RecruiterReview>(`/recruiters/${profile.id}/reviews`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      toast.success("Recruiter review submitted");
      setReviewOpen(false);
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Review failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <main className="page-shell">Loading recruiter...</main>;
  if (!profile) return <main className="page-shell"><EmptyState title="Recruiter unavailable" text="This recruiter profile could not be found." /></main>;

  return (
    <main className="page-shell">
      <PageHeader title={profile.name} eyebrow={profile.company_name || "Recruiter"}>
        <VerificationStatusBadge status={profile.recruiter_verification_status} />
      </PageHeader>

      <section className="grid gap-5 lg:grid-cols-[340px_1fr]">
        <aside className="panel p-5">
          <div className="grid h-28 w-28 place-items-center overflow-hidden rounded-lg border border-black/10 bg-white">
            {profile.company_logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={assetUrl(profile.company_logo_url)} alt={profile.company_name || profile.name} className="h-full w-full object-cover" />
            ) : (
              <Building2 size={32} />
            )}
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <h2 className="text-2xl font-black">{profile.name}</h2>
            {profile.recruiter_verification_status === "VERIFIED" && <BlueTick label="Verified Recruiter" />}
          </div>
          <p className="mt-2 text-sm font-bold text-[#526069]">{profile.designation || "Recruiter"}{profile.department ? `, ${profile.department}` : ""}</p>
          {profile.company_id && (
            <Link href={`/companies/${profile.company_id}`} className="mt-3 inline-flex items-center gap-2 text-sm font-black text-teal-700">
              <Building2 size={16} />
              {profile.company_name}
            </Link>
          )}
          <div className="mt-5 grid gap-3 text-sm font-bold text-[#526069]">
            <span className="flex items-center gap-2"><Star size={16} /> {profile.average_rating.toFixed(1)} from {profile.total_reviews} reviews</span>
            <span className="flex items-center gap-2"><BriefcaseBusiness size={16} /> {profile.active_jobs_count} active jobs</span>
            <span className="flex items-center gap-2"><MessageCircle size={16} /> Recruiter-started chat after shortlist</span>
          </div>
        </aside>

        <div className="grid gap-5">
          {summary && (
            <RatingSummary
              title="Recruiter Rating"
              average={summary.average_overall_rating}
              total={summary.total_reviews}
              rows={[
                { label: "Communication", value: summary.communication_average },
                { label: "Response Time", value: summary.response_time_average },
                { label: "Professionalism", value: summary.professionalism_average },
                { label: "Transparency", value: summary.transparency_average }
              ]}
            />
          )}

          <section className="panel p-5">
            <h2 className="text-xl font-black">Active jobs</h2>
            {jobs.length === 0 ? (
              <p className="mt-3 text-sm font-bold text-[#6b767d]">No active public jobs from this recruiter right now.</p>
            ) : (
              <div className="mt-4 grid gap-4">
                {jobs.map((job) => (
                  <JobCard key={job.id} job={job} detailsHref={`/jobseeker/jobs/${job.id}`} />
                ))}
              </div>
            )}
          </section>

          <section className="panel p-5">
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
              <h2 className="text-xl font-black">Candidate Reviews</h2>
              {user?.role === "JOB_SEEKER" && canReview && !alreadyReviewed && (
                <button className="btn-primary !py-2" type="button" onClick={() => setReviewOpen(true)}>
                  Review Recruiter
                </button>
              )}
            </div>
            <div className="mt-4 grid gap-3">
              {reviews.length === 0 ? (
                <p className="text-sm font-bold text-[#6b767d]">No visible recruiter reviews yet.</p>
              ) : (
                reviews.map((review) => (
                  <ReviewCard
                    key={review.id}
                    reviewerName={review.reviewer_name}
                    title={review.review_title}
                    text={review.review_text}
                    rating={review.overall_rating}
                    createdAt={review.created_at}
                    badges={[
                      `Communication ${review.communication_rating}`,
                      `Response ${review.response_time_rating}`,
                      `Professionalism ${review.professionalism_rating}`,
                      `Transparency ${review.transparency_rating}`
                    ]}
                  />
                ))
              )}
            </div>
            {user?.role === "JOB_SEEKER" && !canReview && (
              <p className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                You can review this recruiter only after being shortlisted or selected.
              </p>
            )}
            {user?.role === "JOB_SEEKER" && alreadyReviewed && (
              <p className="mt-5 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-bold text-emerald-700">
                You have already reviewed this recruiter.
              </p>
            )}
          </section>
        </div>
      </section>

      <ReviewFormModal
        open={reviewOpen}
        mode="recruiter"
        title={`Review ${profile.name}`}
        saving={saving}
        onClose={() => setReviewOpen(false)}
        onSubmit={(payload) => submitReview(payload as RecruiterReviewPayload)}
      />
    </main>
  );
}
