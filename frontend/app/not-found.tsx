import Link from "next/link";

import BrandLogo from "@/components/BrandLogo";

export default function NotFound() {
  return (
    <main className="page-shell">
      <section className="panel mx-auto max-w-lg p-6 text-center md:p-8">
        <div className="mb-5 flex justify-center">
          <BrandLogo size="auth" priority />
        </div>
        <p className="mb-2 text-sm font-black uppercase text-teal-700">404</p>
        <h1 className="text-4xl font-black tracking-normal">Page not found</h1>
        <p className="mt-4 text-sm font-medium leading-7 text-[#526069]">
          The page you are looking for does not exist or may have been moved.
        </p>
        <Link href="/" className="btn-primary mt-6">
          Go back home
        </Link>
      </section>
    </main>
  );
}
