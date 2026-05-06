import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-black/5 bg-[#f7f6f2]/82">
      <div className="mx-auto flex w-[min(1180px,calc(100%-32px))] flex-col gap-3 py-6 text-sm font-bold text-[#6b767d] md:flex-row md:items-center md:justify-between">
        <p>JobSwipe is a final year project demo platform.</p>
        <div className="flex flex-wrap gap-4">
          <Link href="/terms" className="hover:text-[#172026]">
            Terms
          </Link>
          <Link href="/privacy" className="hover:text-[#172026]">
            Privacy
          </Link>
          <span>Support: support@jobswipe.dev</span>
        </div>
      </div>
    </footer>
  );
}
