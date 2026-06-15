import Image from "next/image";

import { cx } from "@/lib/utils";

const logoSizes = {
  nav: "h-11 w-[90px] sm:h-12 sm:w-[112px]",
  auth: "h-20 w-[220px] sm:h-24 sm:w-[260px]",
  hero: "h-24 w-[260px] sm:h-28 sm:w-[320px]",
  footer: "h-16 w-[180px]"
} as const;

type BrandLogoProps = {
  className?: string;
  priority?: boolean;
  size?: keyof typeof logoSizes;
};

export default function BrandLogo({ className, priority = false, size = "nav" }: BrandLogoProps) {
  return (
    <span className={cx("inline-flex min-w-0 items-center", className)}>
      <Image
        alt="Swipe for Success"
        className={cx("block object-contain", logoSizes[size])}
        height={663}
        priority={priority}
        src="/swipe-for-success-logo.png"
        width={1131}
      />
    </span>
  );
}
