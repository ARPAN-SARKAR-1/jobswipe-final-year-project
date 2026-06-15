"use client";

import { Search, X } from "lucide-react";
import { useEffect, useState } from "react";

type SearchBoxProps = {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

export default function SearchBox({ label = "Search", placeholder = "Search", value, onChange, disabled }: SearchBoxProps) {
  const [draft, setDraft] = useState(value);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  useEffect(() => {
    const timer = window.setTimeout(() => onChange(draft), 300);
    return () => window.clearTimeout(timer);
  }, [draft]);

  return (
    <label className="block min-w-0">
      <span className="sr-only">{label}</span>
      <span className="relative block">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8a949a]" size={17} aria-hidden="true" />
        <input
          className="field pl-10 pr-10"
          disabled={disabled}
          placeholder={placeholder}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        {draft && (
          <button
            aria-label="Clear search"
            className="smooth-button absolute right-2 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-md text-[#6b767d] hover:bg-black/5 hover:text-[#172026] active:scale-95"
            onClick={() => setDraft("")}
            type="button"
          >
            <X size={16} aria-hidden="true" />
          </button>
        )}
      </span>
    </label>
  );
}
