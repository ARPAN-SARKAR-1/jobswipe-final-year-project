"use client";

import { useParams } from "next/navigation";

import ChatLayout from "@/components/ChatLayout";

export default function MessageThreadPage() {
  const params = useParams<{ threadId: string }>();
  const selectedThreadId = Number(params.threadId);
  return <ChatLayout selectedThreadId={Number.isFinite(selectedThreadId) ? selectedThreadId : undefined} />;
}
