"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import EmptyState from "@/components/EmptyState";
import ListToolbar from "@/components/ListToolbar";
import PageHeader from "@/components/PageHeader";
import PaginationControls from "@/components/PaginationControls";
import { apiFetch } from "@/lib/api";
import { paginateItems, textMatches } from "@/lib/listing";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { Notification } from "@/types";

export default function NotificationsPage() {
  const { loading } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [query, setQuery] = useState("");
  const [readFilter, setReadFilter] = useState("");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const load = () => {
    apiFetch<Notification[]>("/notifications")
      .then(setNotifications)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Notifications failed"));
  };

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  useEffect(() => {
    setPage(1);
  }, [query, readFilter, sort, pageSize]);

  const filteredNotifications = useMemo(() => {
    return notifications
      .filter((notification) => textMatches(notification, query, [(item) => item.title, (item) => item.message, (item) => item.type]))
      .filter((notification) => {
        if (readFilter === "UNREAD") return !notification.is_read;
        if (readFilter === "READ") return notification.is_read;
        return true;
      })
      .sort((a, b) => {
        if (sort === "oldest") return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        if (sort === "type") return a.type.localeCompare(b.type);
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
  }, [notifications, query, readFilter, sort]);

  const pagedNotifications = useMemo(() => paginateItems(filteredNotifications, page, pageSize), [filteredNotifications, page, pageSize]);

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
        <div className="panel overflow-hidden">
          <ListToolbar
            searchValue={query}
            onSearchChange={setQuery}
            searchPlaceholder="Search notifications"
            filters={[{ label: "Read status", value: readFilter, allLabel: "All notifications", options: [{ label: "Unread", value: "UNREAD" }, { label: "Read", value: "READ" }], onChange: setReadFilter }]}
            sortValue={sort}
            sortOptions={[
              { label: "Newest first", value: "newest" },
              { label: "Oldest first", value: "oldest" },
              { label: "Type", value: "type" }
            ]}
            onSortChange={setSort}
            onReset={() => {
              setQuery("");
              setReadFilter("");
              setSort("newest");
            }}
            resultCount={filteredNotifications.length}
          />
          {filteredNotifications.length === 0 ? (
            <div className="p-5">
              <EmptyState title="No results found" text="No results found for the selected filters." />
            </div>
          ) : (
            <div className="grid gap-3 p-4">
          {pagedNotifications.map((notification) => (
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
          <PaginationControls page={page} pageSize={pageSize} total={filteredNotifications.length} onPageChange={setPage} onPageSizeChange={setPageSize} />
        </div>
      )}
    </main>
  );
}
