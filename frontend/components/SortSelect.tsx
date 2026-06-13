"use client";

import type { SelectOption } from "@/components/FilterSelect";

type SortSelectProps = {
  label?: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
};

export default function SortSelect({ label = "Sort", value, options, onChange }: SortSelectProps) {
  return (
    <label className="block min-w-0">
      <span className="sr-only">{label}</span>
      <select className="field" aria-label={label} value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
