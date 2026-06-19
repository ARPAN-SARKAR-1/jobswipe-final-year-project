"use client";

import { Bot, HelpCircle, LifeBuoy, MessageCircle, Search, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { getStoredUser } from "@/lib/api";
import { getRouteSuggestedTopics, searchHelpTopics, type HelpAudience, type HelpTopic } from "@/lib/helpAssistantData";
import { cx } from "@/lib/utils";
import type { Role } from "@/types";

const roleToAudience: Record<Role, HelpAudience> = {
  JOB_SEEKER: "jobseeker",
  RECRUITER: "recruiter",
  ADMIN: "admin",
  OWNER: "owner"
};

export default function HelpAssistant() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [introVisible, setIntroVisible] = useState(false);
  const [query, setQuery] = useState("");
  const [role, setRole] = useState<HelpAudience>("visitor");
  const [selectedTopic, setSelectedTopic] = useState<HelpTopic | null>(null);
  const isSwipePage = pathname?.startsWith("/jobseeker/swipe");

  useEffect(() => {
    const syncRole = () => {
      const user = getStoredUser();
      setRole(user ? roleToAudience[user.role] : "visitor");
    };
    syncRole();
    window.addEventListener("jobswipe-auth", syncRole);
    window.addEventListener("storage", syncRole);
    return () => {
      window.removeEventListener("jobswipe-auth", syncRole);
      window.removeEventListener("storage", syncRole);
    };
  }, []);

  useEffect(() => {
    const dismissed = window.localStorage.getItem("sfs_help_intro_dismissed");
    if (!dismissed) {
      const timer = window.setTimeout(() => setIntroVisible(true), 900);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  useEffect(() => {
    setSelectedTopic(null);
    setQuery("");
  }, [pathname]);

  const suggestedTopics = useMemo(() => getRouteSuggestedTopics(pathname || "/", role), [pathname, role]);
  const searchResults = useMemo(() => searchHelpTopics(query, role), [query, role]);
  const visibleTopics = query.trim() ? searchResults : suggestedTopics;
  const activeTopic = selectedTopic || visibleTopics[0] || null;

  const dismissIntro = () => {
    setIntroVisible(false);
    window.localStorage.setItem("sfs_help_intro_dismissed", "true");
  };

  return (
    <div
      className={cx(
        "fixed right-3 z-[55] sm:right-5",
        isSwipePage ? "bottom-28 sm:bottom-5" : "bottom-4 sm:bottom-5"
      )}
    >
      {introVisible && !open && (
        <div className="motion-safe-soft mb-3 max-w-[250px] rounded-lg border border-black/10 bg-white p-3 text-sm font-bold text-[#526069] shadow-premium">
          <div className="flex items-start gap-2">
            <Bot className="mt-0.5 shrink-0 text-teal-700" size={18} />
            <div className="min-w-0">
              <p className="font-black text-[#172026]">Need help?</p>
              <p className="mt-1 leading-5">Ask the Swipe Assistant for quick portal guidance.</p>
            </div>
            <button
              className="smooth-button rounded-lg p-1 text-[#6b767d] hover:bg-[#f7f6f2] hover:text-[#172026]"
              type="button"
              aria-label="Dismiss help greeting"
              onClick={dismissIntro}
            >
              <X size={15} />
            </button>
          </div>
        </div>
      )}

      {open && (
        <section
          className={cx(
            "fade-in-up fixed left-3 right-3 bottom-20 mb-0 flex max-h-[min(680px,calc(100vh-112px))] w-auto max-w-[calc(100vw-24px)] flex-col overflow-hidden rounded-lg border border-black/10 bg-white shadow-[0_24px_80px_rgba(23,32,38,0.2)] sm:static sm:mb-3 sm:w-[calc(100vw-32px)] sm:max-w-[400px]",
            isSwipePage && "bottom-36 max-h-[min(620px,calc(100vh-180px))] sm:bottom-auto"
          )}
          aria-labelledby="help-assistant-title"
        >
          <header className="flex items-start justify-between gap-3 border-b border-black/10 bg-[#fbfaf7] p-4">
            <div className="flex min-w-0 items-start gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-teal-50 text-teal-700">
                <Bot size={20} />
              </div>
              <div className="min-w-0">
                <h2 id="help-assistant-title" className="text-base font-black text-[#172026]">
                  Swipe Assistant
                </h2>
                <p className="mt-0.5 text-xs font-bold text-[#6b767d]">Quick help for using the portal</p>
              </div>
            </div>
            <button
              className="smooth-button rounded-lg p-2 text-[#526069] hover:bg-white hover:text-[#172026]"
              type="button"
              aria-label="Close help assistant"
              onClick={() => setOpen(false)}
            >
              <X size={18} />
            </button>
          </header>

          <div className="border-b border-black/10 p-4">
            <label className="sr-only" htmlFor="help-search">Search help topics</label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#8a949a]" size={17} />
              <input
                id="help-search"
                className="field pl-10"
                placeholder="Search help topics..."
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setSelectedTopic(null);
                }}
              />
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <div className="flex flex-wrap gap-2">
              {visibleTopics.map((topic) => (
                <button
                  key={topic.id}
                  className={cx(
                    "smooth-button rounded-lg border px-3 py-2 text-left text-xs font-black",
                    activeTopic?.id === topic.id
                      ? "border-teal-200 bg-teal-50 text-teal-800"
                      : "border-black/10 bg-[#fbfaf7] text-[#526069] hover:bg-white hover:text-[#172026]"
                  )}
                  type="button"
                  onClick={() => setSelectedTopic(topic)}
                >
                  {topic.title}
                </button>
              ))}
            </div>

            {activeTopic ? (
              <article className="mt-4 rounded-lg border border-black/10 bg-[#fbfaf7] p-4">
                <div className="flex items-start gap-2">
                  <HelpCircle className="mt-0.5 shrink-0 text-teal-700" size={18} />
                  <div className="min-w-0">
                    <h3 className="font-black text-[#172026]">{activeTopic.title}</h3>
                    <p className="mt-2 text-sm font-bold leading-6 text-[#526069]">{activeTopic.answer}</p>
                  </div>
                </div>
                {activeTopic.steps && activeTopic.steps.length > 0 && (
                  <ol className="mt-3 grid gap-2 text-sm font-bold leading-6 text-[#526069]">
                    {activeTopic.steps.map((step, index) => (
                      <li key={step} className="flex gap-2">
                        <span className="grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-white text-xs font-black text-teal-700">{index + 1}</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                )}
                {activeTopic.links && activeTopic.links.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {activeTopic.links.map((link) => (
                      <Link key={link.href + link.label} href={link.href} className="btn-secondary !px-3 !py-2 text-xs" onClick={() => setOpen(false)}>
                        {link.label}
                      </Link>
                    ))}
                  </div>
                )}
              </article>
            ) : (
              <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-bold leading-6 text-amber-900">
                I could not find an exact answer. You can raise a support ticket from the Contact page.
              </div>
            )}

            {query.trim() && searchResults.length === 0 && (
              <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-bold leading-6 text-amber-900">
                I could not find an exact answer. You can raise a support ticket from the Contact page.
              </div>
            )}
          </div>

          <footer className="border-t border-black/10 bg-[#fbfaf7] p-4">
            <Link href="/contact" className="btn-primary w-full !py-2 text-sm" onClick={() => setOpen(false)}>
              <LifeBuoy size={17} />
              Raise a support ticket
            </Link>
          </footer>
        </section>
      )}

      <button
        className="smooth-button scale-tap grid h-12 w-12 place-items-center rounded-full bg-[#172026] text-white shadow-[0_18px_48px_rgba(23,32,38,0.26)] hover:-translate-y-1 hover:bg-[#0f171c] focus-visible:outline-white sm:h-14 sm:w-14"
        type="button"
        aria-label={open ? "Close help assistant" : "Open help assistant"}
        onClick={() => {
          setOpen((value) => !value);
          if (introVisible) dismissIntro();
        }}
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>
    </div>
  );
}
