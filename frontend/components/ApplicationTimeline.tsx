"use client";

import { Clock3 } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";

import { apiFetch } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { ApplicationTimelineEvent } from "@/types";

export default function ApplicationTimeline({ applicationId }: { applicationId: number }) {
  const [open, setOpen] = useState(false);
  const [events, setEvents] = useState<ApplicationTimelineEvent[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setOpen(true);
    setLoading(true);
    try {
      setEvents(await apiFetch<ApplicationTimelineEvent[]>(`/applications/${applicationId}/timeline`));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Timeline failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button className="btn-secondary !py-2" type="button" onClick={load}>
        <Clock3 size={16} />
        View Timeline
      </button>
      {open && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4">
          <div className="w-full max-w-lg rounded-lg bg-white p-5 shadow-premium">
            <h2 className="text-xl font-black">Application Timeline</h2>
            <div className="mt-5 grid gap-3">
              {loading ? (
                <p className="text-sm font-bold text-[#6b767d]">Loading timeline...</p>
              ) : events.length === 0 ? (
                <p className="text-sm font-bold text-[#6b767d]">No timeline events yet.</p>
              ) : (
                events.map((event) => (
                  <div key={event.id} className="rounded-lg border border-black/10 bg-[#fbfaf7] p-3">
                    <p className="font-black text-[#172026]">{event.action.replaceAll("_", " ")}</p>
                    <p className="mt-1 text-sm font-bold text-[#6b767d]">
                      {event.old_status ? `${event.old_status} → ${event.new_status || event.old_status}` : event.new_status || "Recorded"}
                    </p>
                    {event.note && <p className="mt-1 text-sm font-medium leading-6 text-[#526069]">{event.note}</p>}
                    <p className="mt-2 text-xs font-black text-[#8a949a]">{formatDate(event.created_at)}</p>
                  </div>
                ))
              )}
            </div>
            <div className="mt-5 flex justify-end">
              <button className="btn-secondary" type="button" onClick={() => setOpen(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
