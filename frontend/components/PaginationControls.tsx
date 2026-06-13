"use client";

type PaginationControlsProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  pageSizeOptions?: number[];
};

export default function PaginationControls({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50]
}: PaginationControlsProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(total, page * pageSize);

  return (
    <div className="flex flex-col justify-between gap-3 border-t border-black/5 bg-[#fbfaf7] p-4 text-sm font-bold text-[#526069] md:flex-row md:items-center">
      <span>
        {total === 0 ? "No results" : `${start}-${end} of ${total}`} · Page {page} of {totalPages}
      </span>
      <div className="flex flex-wrap items-center gap-2">
        <select
          className="field h-10 w-24 py-1 text-sm"
          aria-label="Page size"
          value={pageSize}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
        >
          {pageSizeOptions.map((option) => (
            <option key={option} value={option}>
              {option}/page
            </option>
          ))}
        </select>
        <button className="btn-secondary !px-3 !py-2" disabled={page <= 1} onClick={() => onPageChange(page - 1)} type="button">
          Previous
        </button>
        <button className="btn-secondary !px-3 !py-2" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)} type="button">
          Next
        </button>
      </div>
    </div>
  );
}
