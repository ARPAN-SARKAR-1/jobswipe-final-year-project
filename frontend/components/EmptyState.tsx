import { Inbox } from "lucide-react";

export default function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="panel grid min-h-[260px] place-items-center p-8 text-center">
      <div>
        <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-lg bg-white text-[#172026] shadow-sm">
          <Inbox size={22} />
        </div>
        <h2 className="text-xl font-black">{title}</h2>
        <p className="mt-2 max-w-md text-sm font-medium leading-6 text-[#6b767d]">{text}</p>
      </div>
    </div>
  );
}
