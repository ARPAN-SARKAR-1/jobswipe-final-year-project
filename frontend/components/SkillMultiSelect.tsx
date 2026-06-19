"use client";

import { Check, ChevronDown, Plus, Search, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { commonSkillOptions } from "@/lib/options";
import { cx } from "@/lib/utils";

type SkillMultiSelectProps = {
  label: string;
  selected: string[];
  onChange: (skills: string[]) => void;
  options?: string[];
  placeholder?: string;
  required?: boolean;
};

function cleanSkill(skill: string) {
  return skill.trim().replace(/\s+/g, " ");
}

function dedupe(skills: string[]) {
  const seen = new Set<string>();
  return skills
    .map(cleanSkill)
    .filter((skill) => {
      const key = skill.toLowerCase();
      if (!skill || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

export default function SkillMultiSelect({
  label,
  selected,
  onChange,
  options = commonSkillOptions,
  placeholder = "Select skills",
  required
}: SkillMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [customSkill, setCustomSkill] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);
  const selectedSkills = useMemo(() => dedupe(selected), [selected]);

  const filteredOptions = options.filter((option) => option.toLowerCase().includes(query.toLowerCase()));

  const isSelected = (skill: string) => selectedSkills.some((item) => item.toLowerCase() === skill.toLowerCase());

  const toggle = (skill: string) => {
    if (skill === "Other") return;
    onChange(isSelected(skill) ? selectedSkills.filter((item) => item.toLowerCase() !== skill.toLowerCase()) : dedupe([...selectedSkills, skill]));
  };

  const addCustomSkill = () => {
    const skill = cleanSkill(customSkill);
    if (!skill) return;
    onChange(dedupe([...selectedSkills, skill]));
    setCustomSkill("");
  };

  const remove = (skill: string) => {
    onChange(selectedSkills.filter((item) => item.toLowerCase() !== skill.toLowerCase()));
  };

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!wrapperRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={wrapperRef} className="relative min-w-0 overflow-visible">
      <label className="label">{label}</label>
      <button
        className="field flex min-h-[48px] items-center justify-between gap-3 text-left"
        type="button"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => setOpen((value) => !value)}
      >
        <span className={cx("min-w-0 truncate text-sm font-bold", selectedSkills.length ? "text-[#172026]" : "text-[#8a949b]")}>
          {selectedSkills.length ? `${selectedSkills.length} skills selected` : placeholder}
        </span>
        <ChevronDown className={cx("shrink-0 transition-transform duration-200", open && "rotate-180")} size={18} />
      </button>
      {required && selectedSkills.length === 0 ? <input className="sr-only" required value="" onChange={() => undefined} /> : null}

      <div className="mt-3 flex flex-wrap gap-2">
        {selectedSkills.map((skill) => (
          <span key={skill} className="inline-flex max-w-full min-w-0 items-center gap-1.5 rounded-lg bg-teal-50 px-2.5 py-1 text-xs font-black text-teal-700">
            <span className="min-w-0 break-words">{skill}</span>
            <button type="button" onClick={() => remove(skill)} title={`Remove ${skill}`} aria-label={`Remove ${skill}`} className="shrink-0">
              <X size={13} />
            </button>
          </span>
        ))}
      </div>

      {open && (
        <div className="motion-safe-soft relative z-50 mt-3 rounded-lg border border-black/10 bg-white p-3 shadow-premium sm:absolute sm:left-0 sm:right-0 sm:top-[calc(100%+8px)] sm:mt-0">
          <div className="mb-3 flex items-center gap-2 rounded-lg border border-black/10 bg-[#fbfaf7] px-3 py-2">
            <Search size={16} className="text-[#6b767d]" />
            <input
              className="min-w-0 flex-1 bg-transparent text-base font-bold outline-none sm:text-sm"
              placeholder="Search skills"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>

          <div className="max-h-[min(15rem,48vh)] overflow-y-auto pr-1" role="listbox">
            {filteredOptions.map((skill) =>
              skill === "Other" ? (
                <div key={skill} className="mt-2 rounded-lg bg-[#fbfaf7] p-2">
                  <p className="mb-2 text-xs font-black text-[#526069]">Other</p>
                  <div className="grid gap-2 sm:flex">
                    <input
                      className="field !py-2 text-base sm:text-sm"
                      placeholder="Custom skill"
                      value={customSkill}
                      onChange={(event) => setCustomSkill(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          addCustomSkill();
                        }
                      }}
                    />
                    <button className="btn-secondary !px-3 !py-2" type="button" onClick={addCustomSkill} title="Add custom skill">
                      <Plus size={16} />
                      <span className="sm:sr-only">Add</span>
                    </button>
                  </div>
                </div>
              ) : (
                <label key={skill} className="flex cursor-pointer items-center gap-3 rounded-lg px-2 py-2 text-sm font-bold text-[#526069] hover:bg-[#fbfaf7]">
                  <input type="checkbox" checked={isSelected(skill)} onChange={() => toggle(skill)} className="h-4 w-4 accent-teal-600" />
                  <span className="min-w-0 flex-1 break-words">{skill}</span>
                  {isSelected(skill) && <Check size={15} className="text-teal-700" />}
                </label>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}
