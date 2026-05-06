"use client";

import { Bell } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Notification } from "@/types";

export default function NotificationBell({ enabled }: { enabled: boolean }) {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const unread = notifications.filter((notification) => !notification.is_read).length;

  const load = () => {
    if (!enabled) return;
    apiFetch<Notification[]>("/notifications").then(setNotifications).catch(() => setNotifications([]));
  };

  useEffect(() => {
    load();
  }, [enabled]);

  const markRead = async (notification: Notification) => {
    if (!notification.is_read) {
      await apiFetch(`/notifications/${notification.id}/read`, { method: "PUT" }).catch(() => null);
      load();
    }
  };

  if (!enabled) return null;

  return (
    <div className="relative">
      <button className="btn-secondary !px-3 !py-2" type="button" onClick={() => setOpen((value) => !value)} title="Notifications">
        <Bell size={17} />
        {unread > 0 && <span className="rounded-lg bg-rose-50 px-1.5 py-0.5 text-[11px] font-black text-rose-700">{unread}</span>}
      </button>
      {open && (
        <div className="absolute right-0 top-12 z-50 w-[min(360px,calc(100vw-32px))] overflow-hidden rounded-lg border border-black/10 bg-white shadow-premium">
          <div className="flex items-center justify-between border-b border-black/5 p-3">
            <p className="font-black">Notifications</p>
            <Link href="/notifications" className="text-xs font-black text-teal-700" onClick={() => setOpen(false)}>
              View all
            </Link>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="p-4 text-sm font-bold text-[#6b767d]">No notifications yet.</p>
            ) : (
              notifications.slice(0, 6).map((notification) => {
                const content = (
                  <div className="border-b border-black/5 p-3 hover:bg-[#fbfaf7]">
                    <div className="flex items-start justify-between gap-3">
                      <p className="font-black text-[#172026]">{notification.title}</p>
                      {!notification.is_read && <span className="mt-1 h-2 w-2 rounded-full bg-rose-500" />}
                    </div>
                    <p className="mt-1 text-sm font-bold leading-6 text-[#526069]">{notification.message}</p>
                    <p className="mt-2 text-xs font-black text-[#8a949a]">{formatDate(notification.created_at)}</p>
                  </div>
                );
                return notification.link_url ? (
                  <Link key={notification.id} href={notification.link_url} onClick={() => void markRead(notification)}>
                    {content}
                  </Link>
                ) : (
                  <button key={notification.id} className="w-full text-left" type="button" onClick={() => void markRead(notification)}>
                    {content}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
