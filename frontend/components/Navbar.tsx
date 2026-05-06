"use client";

import { BriefcaseBusiness, LogOut, Menu, Sparkles, UserRound } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import NotificationBell from "@/components/NotificationBell";
import { apiFetch, getStoredUser, logout, roleHome } from "@/lib/api";
import { cx } from "@/lib/utils";
import type { ChatThread, User } from "@/types";

const seekerLinks = [
  ["Dashboard", "/jobseeker/dashboard"],
  ["Swipe", "/jobseeker/swipe"],
  ["Jobs", "/jobseeker/jobs"],
  ["Saved", "/jobseeker/saved"],
  ["Applications", "/jobseeker/applications"],
  ["Messages", "/messages"],
  ["Profile", "/jobseeker/profile"]
];

const recruiterLinks = [
  ["Dashboard", "/recruiter/dashboard"],
  ["Post Job", "/recruiter/jobs/new"],
  ["Applications", "/recruiter/applications"],
  ["Messages", "/messages"],
  ["Company", "/recruiter/company"]
];

const adminLinks = [["Dashboard", "/admin/dashboard"]];

const roleLabels = {
  OWNER: "Owner",
  ADMIN: "Admin",
  RECRUITER: "Recruiter",
  JOB_SEEKER: "Job Seeker"
} as const;

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const sync = () => setUser(getStoredUser());
    sync();
    window.addEventListener("jobswipe-auth", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("jobswipe-auth", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  useEffect(() => {
    if (!user || (user.role !== "RECRUITER" && user.role !== "JOB_SEEKER")) {
      setUnreadCount(0);
      return;
    }
    apiFetch<ChatThread[]>("/chats")
      .then((threads) => setUnreadCount(threads.reduce((total, thread) => total + thread.unread_count, 0)))
      .catch(() => setUnreadCount(0));
  }, [user?.id, user?.role]);

  const links = user?.role === "RECRUITER" ? recruiterLinks : user?.role === "ADMIN" || user?.role === "OWNER" ? adminLinks : seekerLinks;

  const handleLogout = () => {
    logout();
    setUser(null);
    router.push("/");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-black/5 bg-[#f7f6f2]/82 backdrop-blur-xl">
      <div className="mx-auto flex w-[min(1180px,calc(100%-32px))] items-center justify-between py-4">
        <Link href={user ? roleHome(user.role) : "/"} className="flex items-center gap-2 font-black tracking-normal">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-[#172026] text-white">
            <Sparkles size={18} />
          </span>
          <span className="text-lg">JobSwipe</span>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex">
          {user &&
            links.map(([label, href]) => (
              <Link
                key={href}
                href={href}
                className={cx(
                  "rounded-lg px-3 py-2 text-sm font-bold text-[#526069] transition hover:bg-white hover:text-[#172026]",
                  pathname === href && "bg-white text-[#172026] shadow-sm"
                )}
              >
                <span>{label}</span>
                {label === "Messages" && unreadCount > 0 && (
                  <span className="ml-2 rounded-lg bg-rose-50 px-2 py-0.5 text-[11px] font-black text-rose-700">{unreadCount}</span>
                )}
              </Link>
            ))}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          {user ? (
            <>
              <NotificationBell enabled={Boolean(user)} />
              <span className="inline-flex items-center gap-2 rounded-lg bg-white/80 px-3 py-2 text-sm font-bold text-[#526069]">
                <UserRound size={16} />
                {user.name}
              </span>
              <span className="rounded-lg bg-teal-50 px-3 py-2 text-xs font-black text-teal-700">{roleLabels[user.role]}</span>
              <button className="btn-secondary !px-3 !py-2" onClick={handleLogout} type="button" title="Log out">
                <LogOut size={17} />
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn-secondary !px-4 !py-2">
                Login
              </Link>
              <Link href="/register" className="btn-primary !px-4 !py-2">
                <BriefcaseBusiness size={17} />
                Join
              </Link>
            </>
          )}
        </div>

        <button className="btn-secondary !px-3 !py-2 lg:hidden" onClick={() => setOpen((value) => !value)} type="button">
          <Menu size={18} />
        </button>
      </div>

      {open && (
        <div className="mx-auto grid w-[min(1180px,calc(100%-32px))] gap-2 pb-4 lg:hidden">
          {user &&
            links.map(([label, href]) => (
              <Link key={href} href={href} className="rounded-lg bg-white px-3 py-3 text-sm font-bold" onClick={() => setOpen(false)}>
                <span>{label}</span>
                {label === "Messages" && unreadCount > 0 && (
                  <span className="ml-2 rounded-lg bg-rose-50 px-2 py-0.5 text-[11px] font-black text-rose-700">{unreadCount}</span>
                )}
              </Link>
            ))}
          {user ? (
            <div className="flex items-center gap-2">
              <NotificationBell enabled={Boolean(user)} />
              <button className="btn-secondary flex-1" onClick={handleLogout} type="button">
                Logout
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              <Link href="/login" className="btn-secondary">
                Login
              </Link>
              <Link href="/register" className="btn-primary">
                Join
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
