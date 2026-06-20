"use client";

import { AnimatePresence, motion, useReducedMotion, type PanInfo } from "framer-motion";
import { Bookmark, BriefcaseBusiness, CalendarClock, Heart, MapPin, RotateCcw, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import BondBadge from "@/components/BondBadge";
import MatchScoreBadge from "@/components/MatchScoreBadge";
import PageHeader from "@/components/PageHeader";
import ReportModal from "@/components/ReportModal";
import SkillMultiSelect from "@/components/SkillMultiSelect";
import { apiFetch, assetUrl } from "@/lib/api";
import { cx, formatDate, splitSkills } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Job, JobSeekerProfile } from "@/types";

type SwipeAction = "LIKE" | "REJECT" | "SAVE";
type GestureStart = { x: number; y: number; startedAt: number } | null;

const HORIZONTAL_SWIPE_THRESHOLD = 80;
const UP_SWIPE_THRESHOLD = 80;
const DOMINANCE_RATIO = 1.2;

function uniqueJobs(items: Job[]) {
  const seen = new Set<number>();
  return items.filter((job) => {
    if (seen.has(job.id)) return false;
    seen.add(job.id);
    return true;
  });
}

export default function SwipeJobsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [profile, setProfile] = useState<JobSeekerProfile | null>(null);
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(0);
  const [feedbackAction, setFeedbackAction] = useState<SwipeAction | null>(null);
  const [filterSkills, setFilterSkills] = useState<string[]>([]);
  const [swipesSinceRefresh, setSwipesSinceRefresh] = useState(0);
  const [refreshingRecommendations, setRefreshingRecommendations] = useState(false);
  const [recommendationNotice, setRecommendationNotice] = useState("");
  const [dragHint, setDragHint] = useState<SwipeAction | null>(null);
  const feedbackTimer = useRef<number | null>(null);
  const noticeTimer = useRef<number | null>(null);
  const gestureStart = useRef<GestureStart>(null);
  const reduceMotion = useReducedMotion();
  const current = jobs[index];

  const loadFeed = async (options: { silent?: boolean; showUpdatedNotice?: boolean } = {}) => {
    const params = new URLSearchParams({ activeOnly: "true" });
    filterSkills.forEach((skill) => params.append("skills", skill));
    if (options.silent) setRefreshingRecommendations(true);
    try {
      const data = await apiFetch<Job[]>(`/jobs/feed?${params.toString()}`);
      setJobs(uniqueJobs(data));
      setIndex(0);
      if (options.showUpdatedNotice) setRecommendationNotice("Recommendations updated based on your activity.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Feed failed");
    } finally {
      if (options.silent) setRefreshingRecommendations(false);
    }
    apiFetch<JobSeekerProfile>("/jobseeker/profile").then(setProfile).catch(() => setProfile(null));
  };

  useEffect(() => {
    if (loading) return;
    void loadFeed();
  }, [loading]);

  useEffect(() => {
    return () => {
      if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
      if (noticeTimer.current) window.clearTimeout(noticeTimer.current);
    };
  }, []);

  useEffect(() => {
    if (!recommendationNotice) return;
    if (noticeTimer.current) window.clearTimeout(noticeTimer.current);
    noticeTimer.current = window.setTimeout(() => setRecommendationNotice(""), 3500);
  }, [recommendationNotice]);

  const move = async (action: SwipeAction) => {
    if (!current) return;
    if (action === "LIKE" && profile && profile.profile_completion_percentage !== undefined && profile.profile_completion_percentage < 100) {
      toast.error("Complete your profile before applying to jobs.");
      return;
    }
    setFeedbackAction(action);
    try {
      await apiFetch("/swipes", {
        method: "POST",
        body: JSON.stringify({ job_id: current.id, action })
      });
      setDirection(action === "REJECT" ? -1 : action === "SAVE" ? 0 : 1);
      setIndex((value) => value + 1);
      toast.success(action === "LIKE" ? "Applied successfully" : action === "SAVE" ? "Saved for later" : "Skipped");
      const nextSwipeCount = swipesSinceRefresh + 1;
      if (nextSwipeCount >= 3) {
        setSwipesSinceRefresh(0);
        await loadFeed({ silent: true, showUpdatedNotice: true });
      } else {
        setSwipesSinceRefresh(nextSwipeCount);
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Swipe failed");
    } finally {
      if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
      feedbackTimer.current = window.setTimeout(() => setFeedbackAction(null), 220);
    }
  };

  const undo = async () => {
    try {
      await apiFetch("/swipes/undo", { method: "POST" });
      setDirection(0);
      setIndex((value) => Math.max(0, value - 1));
      toast.success("Last swipe undone");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Undo failed");
    }
  };

  const onDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    setDragHint(null);
    if (info.offset.x > HORIZONTAL_SWIPE_THRESHOLD) void move("LIKE");
    if (info.offset.x < -HORIZONTAL_SWIPE_THRESHOLD) void move("REJECT");
  };

  const actionFromDelta = (deltaX: number, deltaY: number, threshold: number): SwipeAction | null => {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    if (deltaY < -threshold && absY > absX * DOMINANCE_RATIO) return "SAVE";
    if (absX > threshold && absX > absY) return deltaX > 0 ? "LIKE" : "REJECT";
    return null;
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
    gestureStart.current = { x: event.clientX, y: event.clientY, startedAt: Date.now() };
  };

  const onPointerMove = (event: React.PointerEvent<HTMLElement>) => {
    if (!gestureStart.current) return;
    const deltaX = event.clientX - gestureStart.current.x;
    const deltaY = event.clientY - gestureStart.current.y;
    setDragHint(actionFromDelta(deltaX, deltaY, 40));
  };

  const onPointerUp = (event: React.PointerEvent<HTMLElement>) => {
    if (!gestureStart.current) return;
    const deltaX = event.clientX - gestureStart.current.x;
    const deltaY = event.clientY - gestureStart.current.y;
    const action = actionFromDelta(deltaX, deltaY, UP_SWIPE_THRESHOLD);
    gestureStart.current = null;
    setDragHint(null);
    if (action === "SAVE") void move("SAVE");
  };

  const onPointerCancel = () => {
    gestureStart.current = null;
    setDragHint(null);
  };

  if (loading) return <main className="page-shell">Loading swipe feed...</main>;
  const profileIncomplete = profile && profile.profile_completion_percentage !== undefined && profile.profile_completion_percentage < 100;

  return (
    <main className="page-shell pb-32 sm:pb-8">
      <PageHeader title="Swipe Jobs" eyebrow="Discover">
        <div className="rounded-lg bg-white px-4 py-2 text-sm font-black text-[#526069]">
          {jobs.length ? `${Math.min(index + 1, jobs.length)} of ${jobs.length} jobs viewed` : "0 jobs viewed"}
        </div>
      </PageHeader>
      {profileIncomplete && (
        <div className="panel mb-5 flex flex-col gap-3 border-amber-200 bg-amber-50 p-4 text-amber-900 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-black">Complete your profile before applying to jobs.</p>
            <p className="mt-1 text-sm font-bold">
              Missing: {(profile.missing_profile_fields || []).slice(0, 5).join(", ") || "required profile details"}.
            </p>
          </div>
          <Link className="btn-primary shrink-0 !py-2" href="/jobseeker/settings/profile">
            Complete profile
          </Link>
        </div>
      )}

      <section className="grid min-w-0 gap-6 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
        <div className="relative z-0 mx-auto grid w-full max-w-full place-items-start sm:max-w-[460px] lg:min-h-[680px] lg:place-items-center">
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
                onPointerUp={onPointerUp}
                onPointerCancel={onPointerCancel}
                initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 24, scale: 0.96 }}
                animate={reduceMotion ? { opacity: 1, x: 0 } : { opacity: 1, y: 0, x: 0, rotate: 0, scale: 1 }}
                exit={reduceMotion ? { opacity: 0 } : { opacity: 0, x: direction * 420, rotate: direction * 16, scale: 0.92 }}
                transition={reduceMotion ? { duration: 0.01 } : { type: "spring", stiffness: 260, damping: 28 }}
                className="relative z-0 w-full max-w-full touch-pan-y cursor-grab rounded-lg border border-black/10 bg-white p-4 shadow-premium transition-shadow duration-300 ease-out active:cursor-grabbing sm:p-5"
              >
                <div
                  className={cx(
                    "pointer-events-none absolute inset-0 rounded-lg opacity-0 transition-opacity duration-200",
                    (dragHint || feedbackAction) === "REJECT" && "bg-rose-500/10 opacity-100",
                    (dragHint || feedbackAction) === "LIKE" && "bg-emerald-500/10 opacity-100",
                    (dragHint || feedbackAction) === "SAVE" && "bg-amber-400/15 opacity-100"
                  )}
                  aria-hidden="true"
                />
                {(dragHint || feedbackAction) && (
                  <div
                    className={cx(
                      "pointer-events-none absolute left-1/2 top-4 z-10 -translate-x-1/2 rounded-lg px-3 py-1 text-xs font-black shadow-sm",
                      (dragHint || feedbackAction) === "REJECT" && "bg-rose-50 text-rose-700",
                      (dragHint || feedbackAction) === "LIKE" && "bg-emerald-50 text-emerald-700",
                      (dragHint || feedbackAction) === "SAVE" && "bg-amber-50 text-amber-700"
                    )}
                    aria-hidden="true"
                  >
                    {(dragHint || feedbackAction) === "REJECT" ? "Skip" : (dragHint || feedbackAction) === "SAVE" ? "Save" : "Apply"}
                  </div>
                )}
                <div className="flex min-w-0 items-start justify-between gap-3">
                  <div className="smooth-hover grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-lg border border-black/10 bg-[#fbfaf7] sm:h-16 sm:w-16">
                    {current.company_logo_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={assetUrl(current.company_logo_url)} alt={current.company_name} className="h-full w-full object-cover" />
                    ) : (
                      <BriefcaseBusiness size={28} />
                    )}
                  </div>
                  <span className="max-w-[160px] break-words rounded-lg bg-teal-50 px-3 py-1 text-xs font-black text-teal-700">{current.work_mode}</span>
                </div>

                <h2 className="mt-6 break-words text-2xl font-black tracking-normal text-[#172026] sm:mt-7 sm:text-3xl">{current.title}</h2>
                <p className="mt-2 break-words text-base font-black text-[#6b767d]">{current.company_name}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <MatchScoreBadge job={current} />
                  {current.recommendation_reason && (
                    <span className="rounded-lg bg-violet-50 px-2.5 py-1 text-xs font-black text-violet-700">
                      {current.recommendation_reason}
                    </span>
                  )}
                  {current.existing_application_status && (
                    <span className="rounded-lg bg-sky-50 px-2.5 py-1 text-xs font-black text-sky-700">
                      Already Applied: {current.existing_application_status}
                    </span>
                  )}
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                  <Info icon={<MapPin size={16} />} label={current.location} />
                  <Info icon={<BriefcaseBusiness size={16} />} label={current.job_type} />
                  <Info icon={<Heart size={16} />} label={current.required_experience_level} />
                  <Info icon={<CalendarClock size={16} />} label={formatDate(current.deadline)} />
                </div>

                <div className="mt-5 rounded-lg bg-[#fbfaf7] p-4">
                  <p className="text-sm font-black text-[#172026]">Salary/stipend</p>
                  <p className="mt-1 text-sm font-bold text-[#6b767d]">{current.salary || "Not disclosed"}</p>
                </div>

                <div className="mt-4">
                  <BondBadge job={current} />
                </div>

                <div className="mt-5 flex flex-wrap gap-2">
                  {(current.required_skills_list?.length ? current.required_skills_list : splitSkills(current.required_skills)).map((skill) => (
                    <span key={skill} className="rounded-lg bg-teal-50 px-3 py-1.5 text-xs font-black text-teal-700">
                      {skill}
                    </span>
                  ))}
                </div>

                <p className="mt-5 max-h-40 overflow-y-auto break-words text-sm font-medium leading-6 text-[#526069] sm:max-h-none">{current.description}</p>
                {current.eligibility && <p className="mt-3 break-words text-sm font-bold leading-6 text-[#172026]">Eligibility: {current.eligibility}</p>}
                {current.career_page_url && (
                  <a className="mt-4 inline-flex break-all text-sm font-black text-teal-700 underline" href={current.career_page_url} target="_blank" rel="noreferrer">
                    Official career link
                  </a>
                )}
                {current.career_link_status === "LINK_SUSPICIOUS" && (
                  <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
                    {current.career_link_warning || "Verify this link before sharing personal information."}
                  </p>
                )}
              </motion.article>
            ) : (
              <div className="w-full">
                <EmptyState title="No active jobs remain" text="Your swipe feed is clear. Try different filters in the jobs list or come back when recruiters post new roles." />
              </div>
            )}
          </AnimatePresence>
        </div>

        <aside className="panel soft-panel relative z-10 max-w-full p-4 sm:p-5">
          <h2 className="text-xl font-black">Swipe controls</h2>
          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <button
              className={cx(
                "btn-secondary scale-tap pointer-events-auto min-w-0 border-rose-200 bg-rose-50 text-rose-700",
                feedbackAction === "REJECT" && "ring-4 ring-rose-100"
              )}
              onClick={() => move("REJECT")}
              disabled={!current}
              type="button"
            >
              <X size={18} />
              Skip
            </button>
            <button
              className={cx(
                "btn-secondary scale-tap pointer-events-auto min-w-0 border-amber-200 bg-amber-50 text-amber-700",
                feedbackAction === "SAVE" && "ring-4 ring-amber-100"
              )}
              onClick={() => move("SAVE")}
              disabled={!current}
              type="button"
            >
              <Bookmark size={18} />
              Save
            </button>
            <button
              className={cx(
                "btn-primary scale-tap pointer-events-auto min-w-0 bg-emerald-600 hover:bg-emerald-700",
                feedbackAction === "LIKE" && "ring-4 ring-emerald-100"
              )}
              onClick={() => move("LIKE")}
              disabled={!current || Boolean(current.existing_application_status) || Boolean(profileIncomplete)}
              type="button"
            >
              <Heart size={18} />
              {current?.existing_application_status ? "Already Applied" : profileIncomplete ? "Complete Profile" : "Apply"}
            </button>
            <button className="btn-secondary scale-tap pointer-events-auto min-w-0" onClick={undo} type="button">
              <RotateCcw size={18} />
              Undo
            </button>
          </div>
          {current && (
            <div className="mt-3">
              <ReportModal jobId={current.id} label="Report Job" />
            </div>
          )}
          <div className="mt-6">
          <SkillMultiSelect label="Skill filters" selected={filterSkills} onChange={setFilterSkills} />
            <button className="btn-secondary scale-tap mt-3 w-full" type="button" onClick={() => void loadFeed()} disabled={refreshingRecommendations}>
              {refreshingRecommendations ? "Updating..." : "Apply skills"}
            </button>
          </div>
          {(recommendationNotice || refreshingRecommendations) && (
            <p className="mt-3 rounded-lg bg-teal-50 p-3 text-xs font-black leading-5 text-teal-800">
              {refreshingRecommendations ? "Updating recommendations..." : recommendationNotice}
            </p>
          )}
          <div className="mt-6 h-2 rounded-lg bg-stone-200">
            <div
              className="h-2 rounded-lg bg-teal-600 transition-[width] duration-300 ease-out"
              style={{ width: jobs.length ? `${Math.min(index, jobs.length) / jobs.length * 100}%` : "0%" }}
            />
          </div>
          <p className="mt-4 text-sm font-bold leading-6 text-[#6b767d]">
            Swipe left to skip, right to apply, up to save. Buttons stay available as a fallback.
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
