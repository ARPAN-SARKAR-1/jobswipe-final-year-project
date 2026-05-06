"use client";

import ChatWorkspace from "@/components/ChatWorkspace";

export default function ChatLayout({ selectedThreadId }: { selectedThreadId?: number }) {
  return <ChatWorkspace selectedThreadId={selectedThreadId} />;
}
