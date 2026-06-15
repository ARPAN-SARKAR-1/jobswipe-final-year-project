import Image from "next/image";

import { cx } from "@/lib/utils";

const logoSizes = {
  auth: "h-20 w-[220px] sm:h-24 sm:w-[260px]",
  hero: "h-24 w-[260px] sm:h-28 sm:w-[320px]",
  footer: "h-14 w-[170px]"
} as const;

type BrandLogoProps = {
  className?: string;
  priority?: boolean;
  size?: "nav" | keyof typeof logoSizes;
};

export default function BrandLogo({ className, priority = false, size = "nav" }: BrandLogoProps) {
  if (size === "nav") {
    return (
      <span className={cx("smooth-hover interactive-lift inline-flex min-w-0 items-center gap-2", className)}>
        <Image
          alt=""
          aria-hidden="true"
          className="block h-9 w-9 shrink-0 object-contain sm:h-10 sm:w-10"
          height={512}
          priority={priority}
          src="/swipe-for-success-icon.png"
          width={512}
        />
        <span className="hidden truncate text-base font-black tracking-normal text-[#172026] sm:inline">Swipe for Success</span>
      </span>
    );
  }

  return (
    <span className={cx("smooth-hover interactive-lift inline-flex min-w-0 items-center", className)}>
      <Image
        alt="Swipe for Success"
        className={cx("block object-contain", logoSizes[size])}
        height={663}
        priority={priority}
        src="/swipe-for-success-logo-transparent.png"
        width={1131}
      />
    </span>
  );
}
