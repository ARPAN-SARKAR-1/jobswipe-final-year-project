"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiFetch, getStoredUser, getToken, roleHome } from "@/lib/api";
import type { Role, User } from "@/types";

export function useAuth(requiredRoles?: Role[]) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(getStoredUser());
  const [loading, setLoading] = useState(true);
  const roleKey = requiredRoles?.join("|") ?? "";

  useEffect(() => {
    let mounted = true;
    const token = getToken();
    if (!token) {
      setLoading(false);
      router.replace("/login");
      return;
    }

    apiFetch<User>("/auth/me")
      .then((freshUser) => {
        if (!mounted) return;
        setUser(freshUser);
        window.localStorage.setItem("jobswipe_user", JSON.stringify(freshUser));
        const allowedRoles = roleKey ? (roleKey.split("|") as Role[]) : undefined;
        if (allowedRoles && !allowedRoles.includes(freshUser.role)) {
          router.replace(roleHome(freshUser.role));
        }
      })
      .catch(() => {
        window.localStorage.removeItem("jobswipe_token");
        window.localStorage.removeItem("jobswipe_user");
        router.replace("/login");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [router, roleKey]);

  return { user, loading };
}
