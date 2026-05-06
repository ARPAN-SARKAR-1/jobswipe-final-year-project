"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import PageHeader from "@/components/PageHeader";
import { apiFetch } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Notification } from "@/types";

export default function NotificationsPage() {
  const { loading } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const load = () => {
    apiFetch<Notification[]>("/notifications")
      .then(setNotifications)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Notifications failed"));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  const markRead = async (id: number) => {
    try {
      await apiFetch(`/notifications/${id}/read`, { method: "PUT" });
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Update failed");
    }
  };

  const markAll = async () => {
    try {
      await apiFetch("/notifications/read-all", { method: "PUT" });
      toast.success("Notifications marked as read");
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Update failed");
    }
  };

  if (loading) return <main className="page-shell">Loading notifications...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Notifications" eyebrow="Updates">
        <button className="btn-secondary" type="button" onClick={markAll}>
          Mark all read
        </button>
      </PageHeader>
      {notifications.length === 0 ? (
        <EmptyState title="No notifications" text="Important application, chat, moderation, and verification updates will appear here." />
      ) : (
        <div className="grid gap-3">
          {notifications.map((notification) => (
            <article key={notification.id} className="panel p-4">
              <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-black">{notification.title}</h2>
                    {!notification.is_read && <span className="rounded-lg bg-rose-50 px-2 py-1 text-xs font-black text-rose-700">Unread</span>}
                  </div>
                  <p className="mt-2 text-sm font-bold leading-6 text-[#526069]">{notification.message}</p>
                  <p className="mt-2 text-xs font-black text-[#8a949a]">{formatDate(notification.created_at)}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {notification.link_url && (
                    <Link className="btn-primary !py-2" href={notification.link_url} onClick={() => markRead(notification.id)}>
                      Open
                    </Link>
                  )}
                  {!notification.is_read && (
                    <button className="btn-secondary !py-2" type="button" onClick={() => markRead(notification.id)}>
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
