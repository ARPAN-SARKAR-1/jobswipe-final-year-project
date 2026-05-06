export default function PageHeader({ title, eyebrow, children }: { title: string; eyebrow?: string; children?: React.ReactNode }) {
  return (
    <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        {eyebrow && <p className="mb-2 text-sm font-black uppercase text-teal-700">{eyebrow}</p>}
        <h1 className="text-3xl font-black tracking-normal text-[#172026] md:text-4xl">{title}</h1>
      </div>
      {children}
    </div>
  );
}
