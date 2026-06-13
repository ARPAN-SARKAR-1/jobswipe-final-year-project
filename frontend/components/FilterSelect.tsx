"use client";

export type SelectOption = {
  label: string;
  value: string;
};

type FilterSelectProps = {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  allLabel?: string;
};

export default function FilterSelect({ label, value, options, onChange, allLabel = "All" }: FilterSelectProps) {
  return (
    <label className="block min-w-0">
      <span className="sr-only">{label}</span>
      <select className="field" aria-label={label} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{allLabel}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
