"use client";

import { AnimatePresence, motion, useReducedMotion, type PanInfo } from "framer-motion";
import { BriefcaseBusiness, CheckCircle2, ExternalLink, FileText, GraduationCap, MessageCircle, UserRound, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { apiFetch, assetUrl } from "@/lib/api";
import { cx, formatDate, splitSkills } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Application } from "@/types";

type RecruiterSwipeAction = "SHORTLIST" | "REJECT";
type GestureStart = { x: number; y: number } | null;
type CandidateApplication = Application & {
  applicant_skills?: string | null;
};

const HORIZONTAL_SWIPE_THRESHOLD = 80;
const REVIEWABLE_STATUSES = new Set(["APPLIED", "VIEWED"]);

function reviewableApplications(applications: CandidateApplication[]) {
  return applications.filter(
    (application) =>
      REVIEWABLE_STATUSES.has(application.status) &&
      application.admin_status === "ACTIVE" &&
      application.job?.moderation_status === "ACTIVE"
  );
}

function readableCategory(category?: string | null) {
  if (!category) return "Category not set";
  return category.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function RecruiterCandidateSwipePage() {
  const { loading } = useAuth(["RECRUITER"]);
  const router = useRouter();
  const [queue, setQueue] = useState<CandidateApplication[]>([]);
  const [totalLoaded, setTotalLoaded] = useState(0);
  const [direction, setDirection] = useState(0);
  const [feedbackAction, setFeedbackAction] = useState<RecruiterSwipeAction | null>(null);
  const [dragHint, setDragHint] = useState<RecruiterSwipeAction | null>(null);
  const [busy, setBusy] = useState(false);
  const gestureStart = useRef<GestureStart>(null);
  const feedbackTimer = useRef<number | null>(null);
  const reduceMotion = useReducedMotion();
  const current = queue[0];

  const load = async () => {
    try {
      const applications = await apiFetch<CandidateApplication[]>("/recruiter/applications");
      const reviewable = reviewableApplications(applications);
      setQueue(reviewable);
      setTotalLoaded(reviewable.length);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Candidate feed failed");
    }
  };

  useEffect(() => {
    if (!loading) void load();
  }, [loading]);

  useEffect(() => {
    return () => {
      if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    };
  }, []);

  const completeAction = async (action: RecruiterSwipeAction) => {
    if (!current || busy) return;
    const status = action === "SHORTLIST" ? "SHORTLISTED" : "REJECTED";
    setBusy(true);
    setFeedbackAction(action);
    try {
      await apiFetch(`/recruiter/applications/${current.id}/status`, {
        method: "PUT",
        body: JSON.stringify({ status })
      });
      setDirection(action === "SHORTLIST" ? 1 : -1);
      setQueue((items) => items.filter((item) => item.id !== current.id));
      toast.success(action === "SHORTLIST" ? "Candidate shortlisted" : "Candidate rejected");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Candidate review failed");
    } finally {
      setBusy(false);
      if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
      feedbackTimer.current = window.setTimeout(() => setFeedbackAction(null), 240);
    }
  };

  const actionFromDelta = (deltaX: number): RecruiterSwipeAction | null => {
    if (deltaX > HORIZONTAL_SWIPE_THRESHOLD) return "SHORTLIST";
    if (deltaX < -HORIZONTAL_SWIPE_THRESHOLD) return "REJECT";
    return null;
  };

  const onDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    setDragHint(null);
    const action = actionFromDelta(info.offset.x);
    if (action) void completeAction(action);
  };

  const isInteractiveTarget = (target: EventTarget | null) => {
    if (!(target instanceof HTMLElement)) return false;
    return Boolean(target.closest("a,button,input,select,textarea,label"));
  };

  const onPointerDown = (event: React.PointerEvent<HTMLElement>) => {
    if (isInteractiveTarget(event.target)) {
      gestureStart.current = null;
      return;
    }
    gestureStart.current = { x: event.clientX, y: event.clientY };
  };

  const onPointerMove = (event: React.PointerEvent<HTMLElement>) => {
    if (!gestureStart.current) return;
    const deltaX = event.clientX - gestureStart.current.x;
    if (Math.abs(deltaX) > 40) setDragHint(deltaX > 0 ? "SHORTLIST" : "REJECT");
  };

  const resetPointer = () => {
    gestureStart.current = null;
    setDragHint(null);
  };

  const startChat = async () => {
    if (!current?.chat_thread_id) return;
    router.push(`/messages/${current.chat_thread_id}`);
  };

  if (loading) return <main className="page-shell">Loading candidate swipe...</main>;

  return (
    <main className="page-shell pb-32 sm:pb-8">
      <PageHeader title="Swipe Candidates" eyebrow="Recruiter review">
        <div className="rounded-lg bg-white px-4 py-2 text-sm font-black text-[#526069]">
          {queue.length ? `${Math.max(totalLoaded - queue.length + 1, 1)} of ${totalLoaded} candidates` : "0 candidates"}
        </div>
      </PageHeader>

      <section className="grid min-w-0 gap-6 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start">
        <div className="relative z-0 mx-auto grid w-full max-w-full place-items-start sm:max-w-[500px] lg:min-h-[680px] lg:place-items-center">
          <AnimatePresence custom={direction} mode="popLayout">
            {current ? (
              <motion.article
                key={current.id}
                custom={direction}
                drag="x"
                dragConstraints={{ left: 0, right: 0 }}
                onDragEnd={onDragEnd}
                onPointerDown={onPointerDown}
                onPointerMove={onPointerMove}
                onPointerUp={resetPointer}
                onPointerCancel={resetPointer}
                initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 24, scale: 0.96 }}
                animate={reduceMotion ? { opacity: 1, x: 0 } : { opacity: 1, y: 0, x: 0, rotate: 0, scale: 1 }}
                exit={reduceMotion ? { opacity: 0 } : { opacity: 0, x: direction * 420, rotate: direction * 14, scale: 0.92 }}
                transition={reduceMotion ? { duration: 0.01 } : { type: "spring", stiffness: 260, damping: 28 }}
                className="relative z-0 w-full max-w-full touch-pan-y cursor-grab rounded-lg border border-black/10 bg-white p-4 shadow-premium transition-shadow duration-300 ease-out active:cursor-grabbing sm:p-5"
              >
                <div
                  className={cx(
                    "pointer-events-none absolute inset-0 rounded-lg opacity-0 transition-opacity duration-200",
                    (dragHint || feedbackAction) === "REJECT" && "bg-rose-500/10 opacity-100",
                    (dragHint || feedbackAction) === "SHORTLIST" && "bg-emerald-500/10 opacity-100"
                  )}
                  aria-hidden="true"
                />
                {(dragHint || feedbackAction) && (
                  <div
                    className={cx(
                      "pointer-events-none absolute left-1/2 top-4 z-10 -translate-x-1/2 rounded-lg px-3 py-1 text-xs font-black shadow-sm",
                      (dragHint || feedbackAction) === "REJECT" && "bg-rose-50 text-rose-700",
                      (dragHint || feedbackAction) === "SHORTLIST" && "bg-emerald-50 text-emerald-700"
                    )}
                    aria-hidden="true"
                  >
                    {(dragHint || feedbackAction) === "SHORTLIST" ? "Shortlist" : "Reject"}
                  </div>
                )}

                <div className="flex min-w-0 items-start justify-between gap-3">
                  <div className="smooth-hover grid h-14 w-14 shrink-0 place-items-center rounded-lg border border-black/10 bg-[#fbfaf7] text-teal-700 sm:h-16 sm:w-16">
                    <UserRound size={30} />
                  </div>
                  <div className="flex flex-wrap justify-end gap-2">
                    <StatusBadge status={current.status} />
                    {current.job?.trusted_posting && <span className="rounded-lg bg-teal-50 px-2.5 py-1 text-xs font-black text-teal-700">Trusted job</span>}
                  </div>
                </div>

                <h2 className="mt-6 break-words text-2xl font-black tracking-normal text-[#172026] sm:mt-7 sm:text-3xl">
                  {current.applicant_name || "Candidate"}
                </h2>
                <p className="mt-2 break-words text-sm font-bold text-[#6b767d]">{current.applicant_email}</p>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Info icon={<GraduationCap size={16} />} label={readableCategory(current.applicant_job_seeker_category)} />
                  <Info icon={<BriefcaseBusiness size={16} />} label={current.applicant_total_experience_years != null ? `${current.applicant_total_experience_years} yrs experience` : "Experience not shared"} />
                  <Info icon={<FileText size={16} />} label={current.applicant_passing_year ? `Passing ${current.applicant_passing_year}` : "Passing year not shared"} />
                  <Info icon={<BriefcaseBusiness size={16} />} label={current.job_title || current.job?.title || "Applied job"} />
                </div>

                <section className="mt-5 rounded-lg bg-[#fbfaf7] p-4">
                  <p className="text-sm font-black text-[#172026]">Applied role</p>
                  <p className="mt-1 break-words text-sm font-bold leading-6 text-[#526069]">
                    {current.job_title || current.job?.title} at {current.job?.company_name || "your company"}
                  </p>
                  <p className="mt-1 text-xs font-bold text-[#6b767d]">Applied {formatDate(current.created_at)}</p>
                </section>

                <section className="mt-5">
                  <p className="text-sm font-black text-[#172026]">Candidate skills</p>
                  {splitSkills(current.applicant_skills).length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {splitSkills(current.applicant_skills).map((skill) => (
                        <span key={skill} className="rounded-lg bg-teal-50 px-3 py-1.5 text-xs font-black text-teal-700">
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-1 text-sm font-bold text-[#6b767d]">Skills were not shared in the profile summary.</p>
                  )}
                </section>

                <div className="mt-5 flex flex-wrap gap-2 text-xs font-black text-[#526069]">
                  {current.applicant_student_verification_status === "STUDENT_VERIFIED" && <span className="rounded-lg bg-emerald-50 px-2.5 py-1 text-emerald-700">Student verified</span>}
                  {current.applicant_graduation_verification_status === "GRADUATION_VERIFIED" && <span className="rounded-lg bg-emerald-50 px-2.5 py-1 text-emerald-700">Graduation verified</span>}
                  {current.applicant_experience_verification_status === "EXPERIENCE_VERIFIED" && <span className="rounded-lg bg-emerald-50 px-2.5 py-1 text-emerald-700">Experience verified</span>}
                </div>

                {current.applicant_has_accessibility_needs && (
                  <div className="mt-5 rounded-lg border border-sky-100 bg-sky-50 p-3 text-sm font-bold leading-6 text-sky-900">
                    <p className="font-black text-sky-700">Candidate-shared accommodation information</p>
                    {splitSkills(current.applicant_accessibility_needs).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {splitSkills(current.applicant_accessibility_needs).map((item) => (
                          <span key={item} className="rounded-lg bg-white px-2.5 py-1 text-xs font-black text-sky-800">
                            {item}
                          </span>
                        ))}
                      </div>
                    )}
                    {current.applicant_accessibility_notes && <p className="mt-2">{current.applicant_accessibility_notes}</p>}
                  </div>
                )}

                <div className="mt-5 flex flex-wrap gap-3">
                  {current.applicant_resume_pdf_url && (
                    <a className="btn-secondary scale-tap !py-2" href={assetUrl(current.applicant_resume_pdf_url)} target="_blank" rel="noreferrer">
                      <ExternalLink size={16} />
                      Resume
                    </a>
                  )}
                  {current.applicant_github_url && (
                    <a className="btn-secondary scale-tap !py-2" href={current.applicant_github_url} target="_blank" rel="noreferrer">
                      <ExternalLink size={16} />
                      GitHub
                    </a>
                  )}
                  {current.chat_thread_id && (
                    <button className="btn-primary scale-tap !py-2" type="button" onClick={startChat}>
                      <MessageCircle size={16} />
                      Open Chat
                    </button>
                  )}
                </div>
              </motion.article>
            ) : (
              <div className="w-full">
                <EmptyState title="No candidates available for swipe review right now." text="New applicants with active applications will appear here for quick review." />
              </div>
            )}
          </AnimatePresence>
        </div>

        <aside className="panel soft-panel relative z-10 max-w-full p-4 sm:p-5">
          <h2 className="text-xl font-black">Candidate controls</h2>
          <p className="mt-3 text-sm font-bold leading-6 text-[#6b767d]">Swipe right to shortlist, left to reject. Buttons remain available as a fallback.</p>
          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <button
              className={cx("btn-secondary scale-tap pointer-events-auto min-w-0 border-rose-200 bg-rose-50 text-rose-700", feedbackAction === "REJECT" && "ring-4 ring-rose-100")}
              type="button"
              onClick={() => void completeAction("REJECT")}
              disabled={!current || busy}
            >
              <X size={18} />
              Reject
            </button>
            <button
              className={cx("btn-primary scale-tap pointer-events-auto min-w-0 bg-emerald-600 hover:bg-emerald-700", feedbackAction === "SHORTLIST" && "ring-4 ring-emerald-100")}
              type="button"
              onClick={() => void completeAction("SHORTLIST")}
              disabled={!current || busy}
            >
              <CheckCircle2 size={18} />
              Shortlist
            </button>
          </div>
          <div className="mt-6 h-2 rounded-lg bg-stone-200">
            <div
              className="h-2 rounded-lg bg-teal-600 transition-[width] duration-300 ease-out"
              style={{ width: totalLoaded ? `${((totalLoaded - queue.length) / totalLoaded) * 100}%` : "0%" }}
            />
          </div>
          <p className="mt-4 text-sm font-bold leading-6 text-[#6b767d]">
            Shortlisted candidates can move into the existing controlled chat workflow. Withdrawn, rejected, shortlisted, paused, or removed applications are not shown here.
          </p>
        </aside>
      </section>
    </main>
  );
}

function Info({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="smooth-hover flex min-w-0 items-center gap-2 rounded-lg border border-black/10 bg-[#fbfaf7] px-3 py-3 text-sm font-black text-[#526069]">
      <span className="shrink-0">{icon}</span>
      <span className="min-w-0 break-words">{label}</span>
    </div>
  );
}
