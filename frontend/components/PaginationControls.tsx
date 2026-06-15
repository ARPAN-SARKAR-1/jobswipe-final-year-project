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
    <div className="motion-safe-soft flex flex-col justify-between gap-3 border-t border-black/5 bg-[#fbfaf7]/92 p-3 text-sm font-bold text-[#526069] transition-colors duration-300 ease-out sm:p-4 md:flex-row md:items-center">
      <span className="text-center md:text-left">
        {total === 0 ? "No results" : `${start}-${end} of ${total}`} - Page {page} of {totalPages}
      </span>
      <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto sm:flex-wrap sm:items-center">
        <select
          className="field col-span-2 h-10 w-full py-1 text-sm sm:w-28"
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
        <button className="btn-secondary scale-tap w-full !px-3 !py-2 sm:w-auto" disabled={page <= 1} onClick={() => onPageChange(page - 1)} type="button">
          Previous
        </button>
        <button className="btn-secondary scale-tap w-full !px-3 !py-2 sm:w-auto" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)} type="button">
          Next
        </button>
      </div>
    </div>
  );
}
