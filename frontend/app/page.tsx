import {
  BriefcaseBusiness,
  Building2,
  FileText,
  LayoutDashboard,
  ListFilter,
  ShieldCheck,
  Sparkles,
  UserRoundCheck
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";

import BrandLogo from "@/components/BrandLogo";

const features: Array<{ title: string; description: string; icon: LucideIcon }> = [
  {
    title: "Swipe-Based Job Discovery",
    description: "Review focused job cards and take action with Skip, Save, or Apply.",
    icon: Sparkles
  },
  {
    title: "Verified Hiring Network",
    description: "Company, recruiter, and job seeker verification helps reduce fake profiles and misleading job posts.",
    icon: ShieldCheck
  },
  {
    title: "Smart Filters and Search",
    description: "Filter jobs, applicants, companies, and applications by role, skill, status, and verification.",
    icon: ListFilter
  },
  {
    title: "Privacy-Controlled Profiles",
    description: "Job seekers can manage public, recruiter-only, and private profile sections.",
    icon: UserRoundCheck
  },
  {
    title: "Secure Document Uploads",
    description: "Resumes, certificates, and verification proofs are size-limited and protected by role-based access.",
    icon: FileText
  },
  {
    title: "Recruiter and Admin Workflows",
    description: "Recruiters manage jobs and applicants, while Admins and Owners review verification and moderation queues.",
    icon: Building2
  }
];

const stats = [
  ["4", "role-based portals"],
  ["3", "job seeker categories"],
  ["Verified", "company and recruiter badges"],
  ["Private", "document controls"]
];

export default function LandingPage() {
  return (
    <main>
      <section className="relative overflow-hidden border-b border-black/5">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(20,184,166,0.13),rgba(255,255,255,0.3),rgba(244,63,94,0.10))]" />
        <div className="page-shell relative grid min-h-[calc(100vh-73px)] items-center gap-10 py-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="fade-in-up">
            <BrandLogo className="mb-6" priority size="hero" />
            <div className="smooth-card mb-5 inline-flex items-center gap-2 rounded-lg border border-black/10 bg-white/80 px-3 py-2 text-sm font-black text-teal-700 shadow-sm">
              <BriefcaseBusiness size={16} />
              Verified career platform
            </div>
            <h1 className="max-w-3xl text-5xl font-black tracking-normal text-[#172026] md:text-7xl">Swipe Less. Apply Smarter.</h1>
            <p className="mt-6 max-w-2xl text-lg font-medium leading-8 text-[#526069]">
              Swipe for Success helps job seekers discover opportunities one card at a time, and gives recruiters a smarter way to find the right talent.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/login" className="btn-primary scale-tap">
                Start Swiping
              </Link>
              <Link href="/login" className="btn-secondary scale-tap">
                Post a Job
              </Link>
            </div>
          </div>

          <div className="fade-in-up relative min-h-[540px]">
            <div className="motion-safe-soft absolute left-[8%] top-10 h-[430px] w-[78%] rotate-[-7deg] rounded-lg border border-black/10 bg-white/70 p-5 shadow-premium" />
            <div className="motion-safe-soft absolute right-[2%] top-20 h-[430px] w-[78%] rotate-[6deg] rounded-lg border border-black/10 bg-white/70 p-5 shadow-premium" />
            <div className="motion-safe-soft absolute left-1/2 top-3 w-[min(390px,88vw)] -translate-x-1/2 rounded-lg border border-black/10 bg-white p-5 shadow-premium">
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
                  <div key={item} className="smooth-hover rounded-lg border border-black/10 bg-[#fbfaf7] px-3 py-3 text-sm font-black text-[#526069]">
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
                <span className="smooth-button grid h-12 place-items-center rounded-lg bg-rose-50 font-black text-rose-600">Skip</span>
                <span className="smooth-button grid h-12 place-items-center rounded-lg bg-amber-50 font-black text-amber-700">Save</span>
                <span className="smooth-button grid h-12 place-items-center rounded-lg bg-emerald-50 font-black text-emerald-700">Apply</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="page-shell">
        <div className="fade-in-up mb-10 grid gap-3 rounded-lg border border-black/10 bg-white/70 p-4 shadow-sm sm:grid-cols-2 lg:grid-cols-4">
          {stats.map(([value, label]) => (
            <div key={label} className="smooth-card rounded-lg bg-[#fbfaf7] px-4 py-5">
              <p className="text-2xl font-black text-[#172026]">{value}</p>
              <p className="mt-1 text-sm font-bold text-[#6b767d]">{label}</p>
            </div>
          ))}
        </div>
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="mb-2 text-sm font-black uppercase text-teal-700">Features</p>
            <h2 className="text-3xl font-black tracking-normal md:text-4xl">Built for trusted hiring workflows</h2>
          </div>
          <LayoutDashboard className="hidden text-[#172026] md:block" size={34} />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {features.map(({ title, description, icon: Icon }) => (
            <div key={title} className="panel smooth-card p-5">
              <div className="smooth-hover mb-5 grid h-10 w-10 place-items-center rounded-lg bg-white text-[#172026] shadow-sm">
                <Icon size={18} />
              </div>
              <h3 className="text-lg font-black">{title}</h3>
              <p className="mt-3 text-sm font-medium leading-6 text-[#526069]">{description}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
