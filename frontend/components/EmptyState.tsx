import { Inbox } from "lucide-react";

import { cx } from "@/lib/utils";

export default function EmptyState({ title, text, compact = false }: { title: string; text: string; compact?: boolean }) {
  return (
    <div
      className={cx(
        "grid place-items-center text-center",
        compact ? "fade-in-up min-h-[190px] rounded-lg border border-dashed border-black/10 bg-white/70 p-6" : "panel fade-in-up min-h-[260px] p-8"
      )}
    >
      <div>
        <div className="smooth-hover mx-auto mb-4 grid h-12 w-12 place-items-center rounded-lg bg-white text-[#172026] shadow-sm">
          <Inbox size={22} />
        </div>
        <h2 className="text-xl font-black">{title}</h2>
        <p className="mt-2 max-w-md text-sm font-medium leading-6 text-[#6b767d]">{text}</p>
      </div>
    </div>
  );
}
