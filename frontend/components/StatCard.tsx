import type { LucideIcon } from "lucide-react";

export default function StatCard({ label, value, icon: Icon }: { label: string; value: string | number; icon: LucideIcon }) {
  return (
    <div className="panel smooth-card p-5">
      <div className="smooth-hover mb-5 flex h-10 w-10 items-center justify-center rounded-lg bg-[#172026] text-white shadow-sm">
        <Icon size={18} />
      </div>
      <p className="text-3xl font-black tracking-normal text-[#172026]">{value}</p>
      <p className="mt-1 text-sm font-bold text-[#6b767d]">{label}</p>
    </div>
  );
}
