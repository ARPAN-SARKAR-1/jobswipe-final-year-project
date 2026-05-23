"use client";

import { Building2, MapPin, Star } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import BlueTick from "@/components/BlueTick";
import EmptyState from "@/components/EmptyState";
import PageHeader from "@/components/PageHeader";
import VerificationStatusBadge from "@/components/VerificationStatusBadge";
import { apiFetch, assetUrl } from "@/lib/api";
import type { Company } from "@/types";

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Company[]>("/companies")
      .then(setCompanies)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Companies failed"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <main className="page-shell">Loading companies...</main>;

  return (
    <main className="page-shell">
      <PageHeader title="Companies" eyebrow="Verified employers" />
      {companies.length === 0 ? (
        <EmptyState title="No companies found" text="Recruiter company profiles will appear here after setup." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {companies.map((company) => (
            <Link key={company.id} href={`/companies/${company.id}`} className="panel block p-5 transition hover:-translate-y-0.5 hover:border-teal-300">
              <div className="flex items-start gap-4">
                <div className="grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-lg border border-black/10 bg-white">
                  {company.company_logo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={assetUrl(company.company_logo_url)} alt={company.company_name} className="h-full w-full object-cover" />
                  ) : (
                    <Building2 size={26} />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-xl font-black text-[#172026]">{company.company_name}</h2>
                    {company.verification_status === "VERIFIED" && <BlueTick label="Verified Company" />}
                  </div>
                  <p className="mt-1 text-sm font-bold text-[#6b767d]">{company.industry || company.company_type}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <VerificationStatusBadge status={company.verification_status} />
                    <span className="inline-flex items-center gap-1 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-black text-amber-800">
                      <Star size={13} /> {company.average_rating.toFixed(1)} ({company.total_reviews})
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-4 grid gap-2 text-sm font-bold text-[#526069] sm:grid-cols-2">
                <span className="flex items-center gap-2">
                  <MapPin size={16} /> {company.headquarters_location || "Location not added"}
                </span>
                <span>{company.active_jobs_count} active jobs</span>
                <span>{company.recruiter_count} recruiters</span>
                <span>{company.company_type}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
