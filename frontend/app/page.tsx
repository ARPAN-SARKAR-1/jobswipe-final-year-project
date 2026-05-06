import {
  Bookmark,
  BriefcaseBusiness,
  Building2,
  FileText,
  Github,
  LayoutDashboard,
  ListFilter,
  ShieldCheck,
  Sparkles
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";

const features: Array<[string, LucideIcon]> = [
  ["Tinder-style job swipe", Sparkles],
  ["Smart job filters", ListFilter],
  ["Resume PDF upload", FileText],
  ["GitHub profile link", Github],
  ["Application tracking", Bookmark],
  ["Recruiter dashboard", Building2],
  ["Admin dashboard", ShieldCheck]
];

export default function LandingPage() {
  return (
    <main>
      <section className="relative overflow-hidden border-b border-black/5">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(20,184,166,0.13),rgba(255,255,255,0.3),rgba(244,63,94,0.10))]" />
        <div className="page-shell relative grid min-h-[calc(100vh-73px)] items-center gap-10 py-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-lg border border-black/10 bg-white/80 px-3 py-2 text-sm font-black text-teal-700">
              <BriefcaseBusiness size={16} />
              Final year full-stack project
            </div>
            <h1 className="max-w-3xl text-5xl font-black tracking-normal text-[#172026] md:text-7xl">Swipe Less. Apply Smarter.</h1>
            <p className="mt-6 max-w-2xl text-lg font-medium leading-8 text-[#526069]">
              JobSwipe turns job discovery into a focused one-card-at-a-time experience, helping job seekers avoid endless scrolling while recruiters get cleaner application intent.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/login" className="btn-primary">
                Start Swiping
              </Link>
              <Link href="/login" className="btn-secondary">
                Post a Job
              </Link>
            </div>
          </div>

          <div className="relative min-h-[540px]">
            <div className="absolute left-[8%] top-10 h-[430px] w-[78%] rotate-[-7deg] rounded-lg border border-black/10 bg-white/70 p-5 shadow-premium" />
            <div className="absolute right-[2%] top-20 h-[430px] w-[78%] rotate-[6deg] rounded-lg border border-black/10 bg-white/70 p-5 shadow-premium" />
            <div className="absolute left-1/2 top-3 w-[min(390px,88vw)] -translate-x-1/2 rounded-lg border border-black/10 bg-white p-5 shadow-premium">
              <div className="flex items-start justify-between gap-4">
                <div className="grid h-14 w-14 place-items-center rounded-lg bg-[#172026] text-white">
                  <Building2 size={24} />
                </div>
                <span className="rounded-lg bg-emerald-50 px-3 py-1 text-xs font-black text-emerald-700">92% match</span>
              </div>
              <h2 className="mt-8 text-3xl font-black tracking-normal text-[#172026]">Python Backend Intern</h2>
              <p className="mt-2 font-bold text-[#6b767d]">NovaWorks Labs</p>
              <div className="mt-6 grid grid-cols-2 gap-3">
                {["Hybrid", "Bengaluru", "Fresher", "INR 25k/mo"].map((item) => (
                  <div key={item} className="rounded-lg border border-black/10 bg-[#fbfaf7] px-3 py-3 text-sm font-black text-[#526069]">
                    {item}
                  </div>
                ))}
              </div>
              <div className="mt-6 flex flex-wrap gap-2">
                {["Python", "SQL", "Cloud"].map((skill) => (
                  <span key={skill} className="rounded-lg bg-teal-50 px-3 py-1.5 text-xs font-black text-teal-700">
                    {skill}
                  </span>
                ))}
              </div>
              <p className="mt-6 text-sm font-medium leading-6 text-[#526069]">
                Build APIs, learn production workflows, and work on real product features with a senior engineering team.
              </p>
              <div className="mt-7 grid grid-cols-3 gap-3">
                <span className="grid h-12 place-items-center rounded-lg bg-rose-50 font-black text-rose-600">Skip</span>
                <span className="grid h-12 place-items-center rounded-lg bg-amber-50 font-black text-amber-700">Save</span>
                <span className="grid h-12 place-items-center rounded-lg bg-emerald-50 font-black text-emerald-700">Apply</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="page-shell">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="mb-2 text-sm font-black uppercase text-teal-700">Features</p>
            <h2 className="text-3xl font-black tracking-normal md:text-4xl">Built for real placement workflows</h2>
          </div>
          <LayoutDashboard className="hidden text-[#172026] md:block" size={34} />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {features.map(([label, Icon]) => (
            <div key={label} className="panel p-5">
              <div className="mb-5 grid h-10 w-10 place-items-center rounded-lg bg-white text-[#172026] shadow-sm">
                <Icon size={18} />
              </div>
              <h3 className="text-lg font-black">{label}</h3>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
