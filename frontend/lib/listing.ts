export function textMatches<T>(item: T, query: string, selectors: Array<(item: T) => unknown>) {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return true;
  return selectors.some((selector) => String(selector(item) ?? "").toLowerCase().includes(normalized));
}

export function paginateItems<T>(items: T[], page: number, pageSize: number) {
  return items.slice((page - 1) * pageSize, page * pageSize);
}

export function clampPage(page: number, total: number, pageSize: number) {
  return Math.min(Math.max(page, 1), Math.max(1, Math.ceil(total / pageSize)));
}
