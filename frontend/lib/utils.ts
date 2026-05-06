export function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

export function splitSkills(skills?: string | string[] | null) {
  const values = Array.isArray(skills) ? skills : (skills || "").split(",");
  const seen = new Set<string>();
  return values
    .map((skill) => skill.trim())
    .filter((skill) => {
      const key = skill.toLowerCase();
      if (!skill || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

export function formatBondYears(years?: number | null) {
  if (years === undefined || years === null) return "";
  const value = Number.isInteger(years) ? String(years) : String(years);
  return `${value} ${years === 1 ? "year" : "years"}`;
}
