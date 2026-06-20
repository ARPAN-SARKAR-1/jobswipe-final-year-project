type RequiredLabelProps = {
  label: string;
  required?: boolean;
  hint?: string;
  htmlFor?: string;
  className?: string;
};

export default function RequiredLabel({ label, required = false, hint, htmlFor, className = "" }: RequiredLabelProps) {
  return (
    <label className={`label inline-flex flex-wrap items-center gap-1 ${className}`} htmlFor={htmlFor}>
      <span>{label}</span>
      {required && (
        <>
          <span className="text-rose-600" aria-hidden="true">
            *
          </span>
          <span className="sr-only"> required</span>
        </>
      )}
      {hint && <span className="text-xs font-bold normal-case text-[#8a949a]">{hint}</span>}
    </label>
  );
}
