"use client";

import { AnimatePresence, motion, type PanInfo } from "framer-motion";
import { Bookmark, BriefcaseBusiness, CalendarClock, Heart, MapPin, RotateCcw, X } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import BondBadge from "@/components/BondBadge";
import MatchScoreBadge from "@/components/MatchScoreBadge";
import PageHeader from "@/components/PageHeader";
import ReportModal from "@/components/ReportModal";
import SkillMultiSelect from "@/components/SkillMultiSelect";
import { apiFetch, assetUrl } from "@/lib/api";
import { formatDate, splitSkills } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Job } from "@/types";

type SwipeAction = "LIKE" | "REJECT" | "SAVE";

export default function SwipeJobsPage() {
  const { loading } = useAuth(["JOB_SEEKER"]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(0);
  const [filterSkills, setFilterSkills] = useState<string[]>([]);
  const current = jobs[index];

  const loadFeed = () => {
    const params = new URLSearchParams({ activeOnly: "true" });
    filterSkills.forEach((skill) => params.append("skills", skill));
    apiFetch<Job[]>((`/jobs/feed?${params.toString()}`))
      .then((data) => {
        setJobs(data);
        setIndex(0);
      })
      .catch((error) => toast.error(error instanceof Error ? error.message : "Feed failed"));
  };

  useEffect(() => {
    if (loading) return;
    loadFeed();
  }, [loading]);

  const move = async (action: SwipeAction) => {
    if (!current) return;
    try {
      await apiFetch("/swipes", {
        method: "POST",
        body: JSON.stringify({ job_id: current.id, action })
      });
      setDirection(action === "REJECT" ? -1 : 1);
      setIndex((value) => value + 1);
      toast.success(action === "LIKE" ? "Applied successfully" : action === "SAVE" ? "Saved for later" : "Skipped");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Swipe failed");
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
    if (info.offset.x > 130) void move("LIKE");
    if (info.offset.x < -130) void move("REJECT");
  };

  if (loading) return <main className="page-shell">Loading swipe feed...</main>;

  return (
    <main className="page-shell pb-24 sm:pb-8">
      <PageHeader title="Swipe Jobs" eyebrow="Discover">
        <div className="rounded-lg bg-white px-4 py-2 text-sm font-black text-[#526069]">
          {jobs.length ? `${Math.min(index + 1, jobs.length)} of ${jobs.length} jobs viewed` : "0 jobs viewed"}
        </div>
      </PageHeader>

      <section className="grid min-w-0 gap-6 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
        <div className="relative mx-auto grid min-h-[620px] w-full max-w-full place-items-center sm:min-h-[680px] sm:max-w-[460px]">
          <AnimatePresence custom={direction} mode="popLayout">
            {current ? (
              <motion.article
                key={current.id}
                custom={direction}
                drag="x"
                dragConstraints={{ left: 0, right: 0 }}
                onDragEnd={onDragEnd}
                initial={{ opacity: 0, y: 24, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, x: 0, rotate: 0, scale: 1 }}
                exit={{ opacity: 0, x: direction * 420, rotate: direction * 16, scale: 0.92 }}
                transition={{ type: "spring", stiffness: 260, damping: 28 }}
                className="absolute w-full max-w-full cursor-grab rounded-lg border border-black/10 bg-white p-4 shadow-premium active:cursor-grabbing sm:p-5"
              >
                <div className="flex min-w-0 items-start justify-between gap-3">
                  <div className="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-lg border border-black/10 bg-[#fbfaf7] sm:h-16 sm:w-16">
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
              </motion.article>
            ) : (
              <div className="w-full">
                <EmptyState title="No active jobs remain" text="Your swipe feed is clear. Try different filters in the jobs list or come back when recruiters post new roles." />
              </div>
            )}
          </AnimatePresence>
        </div>

        <aside className="panel max-w-full p-4 sm:p-5">
          <h2 className="text-xl font-black">Swipe controls</h2>
          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <button className="btn-secondary min-w-0 border-rose-200 bg-rose-50 text-rose-700" onClick={() => move("REJECT")} disabled={!current} type="button">
              <X size={18} />
              Reject
            </button>
            <button className="btn-secondary min-w-0 border-amber-200 bg-amber-50 text-amber-700" onClick={() => move("SAVE")} disabled={!current} type="button">
              <Bookmark size={18} />
              Save
            </button>
            <button className="btn-primary min-w-0 bg-emerald-600 hover:bg-emerald-700" onClick={() => move("LIKE")} disabled={!current || Boolean(current.existing_application_status)} type="button">
              <Heart size={18} />
              {current?.existing_application_status ? "Already Applied" : "Apply"}
            </button>
            <button className="btn-secondary min-w-0" onClick={undo} type="button">
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
            <button className="btn-secondary mt-3 w-full" type="button" onClick={loadFeed}>
              Apply skills
            </button>
          </div>
          <div className="mt-6 h-2 rounded-lg bg-stone-200">
            <div className="h-2 rounded-lg bg-teal-600" style={{ width: jobs.length ? `${Math.min(index, jobs.length) / jobs.length * 100}%` : "0%" }} />
          </div>
          <p className="mt-4 text-sm font-bold leading-6 text-[#6b767d]">
            Drag the card left to skip or right to apply. Saved cards move into your saved jobs history for later review.
          </p>
        </aside>
      </section>
    </main>
  );
}

function Info({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex min-w-0 items-center gap-2 rounded-lg border border-black/10 bg-[#fbfaf7] px-3 py-3 text-sm font-black text-[#526069]">
      <span className="shrink-0">{icon}</span>
      <span className="min-w-0 break-words">{label}</span>
    </div>
  );
}
