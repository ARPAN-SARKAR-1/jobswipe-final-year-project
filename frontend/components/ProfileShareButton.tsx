"use client";

import { Copy, Share2 } from "lucide-react";
import toast from "react-hot-toast";

export default function ProfileShareButton({ href }: { href: string }) {
  const copy = async () => {
    const url = href.startsWith("http") ? href : `${window.location.origin}${href}`;
    try {
      await navigator.clipboard.writeText(url);
      toast.success("Profile link copied");
    } catch {
      toast.error("Could not copy profile link");
    }
  };

  return (
    <button className="btn-secondary !px-3 !py-2" type="button" onClick={copy}>
      <Share2 size={16} />
      <Copy size={14} />
      Share
    </button>
  );
}
