import Link from "next/link";

import BrandLogo from "@/components/BrandLogo";

export default function Footer() {
  return (
    <footer className="border-t border-black/5 bg-[#f7f6f2]/86 backdrop-blur-xl">
      <div className="mx-auto flex w-[min(1180px,calc(100%-32px))] flex-col gap-3 py-6 text-sm font-bold text-[#6b767d] md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 flex-col gap-2">
          <BrandLogo size="footer" />
          <p>Verified jobs. Trusted hiring. One swipe at a time.</p>
        </div>
        <div className="flex flex-wrap gap-4">
          <Link href="/" className="smooth-hover font-black hover:-translate-y-0.5 hover:text-[#172026]">
            Home
          </Link>
          <Link href="/terms" className="smooth-hover font-black hover:-translate-y-0.5 hover:text-[#172026]">
            Terms
          </Link>
          <Link href="/privacy" className="smooth-hover font-black hover:-translate-y-0.5 hover:text-[#172026]">
            Privacy
          </Link>
          <Link href="/contact" className="smooth-hover font-black hover:-translate-y-0.5 hover:text-[#172026]">
            Contact
          </Link>
        </div>
      </div>
    </footer>
  );
}
