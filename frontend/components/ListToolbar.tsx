"use client";

import FilterSelect, { type SelectOption } from "@/components/FilterSelect";
import SearchBox from "@/components/SearchBox";
import SortSelect from "@/components/SortSelect";

export type ToolbarFilter = {
  label: string;
  value: string;
  allLabel?: string;
  options: SelectOption[];
  onChange: (value: string) => void;
};

type ListToolbarProps = {
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder: string;
  filters?: ToolbarFilter[];
  sortValue: string;
  sortOptions: SelectOption[];
  onSortChange: (value: string) => void;
  onReset: () => void;
  resultCount?: number;
};

export default function ListToolbar({
  searchValue,
  onSearchChange,
  searchPlaceholder,
  filters = [],
  sortValue,
  sortOptions,
  onSortChange,
  onReset,
  resultCount
}: ListToolbarProps) {
  return (
    <div className="border-b border-black/5 bg-[#fbfaf7]/92 p-3 transition-colors duration-300 ease-out sm:p-4">
      <div className="grid min-w-0 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="min-w-0 md:col-span-2">
          <SearchBox placeholder={searchPlaceholder} value={searchValue} onChange={onSearchChange} />
        </div>
        {filters.map((filter) => (
          <FilterSelect key={filter.label} {...filter} />
        ))}
        <SortSelect value={sortValue} options={sortOptions} onChange={onSortChange} />
      </div>
      <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <span className="text-xs font-black uppercase text-[#8a949a]">{typeof resultCount === "number" ? `${resultCount} results` : "Filters"}</span>
        <button className="btn-secondary w-full !px-3 !py-2 text-sm sm:w-auto" type="button" onClick={onReset}>
          Reset filters
        </button>
      </div>
    </div>
  );
}
