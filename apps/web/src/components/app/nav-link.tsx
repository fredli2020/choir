"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

type NavLinkProps = {
  href: string;
  icon: ReactNode;
  label: string;
};

export function NavLink({ href, icon, label }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm font-semibold transition-all duration-300",
        isActive
          ? "border-primary/15 bg-primary text-primary-foreground shadow-[0_16px_28px_rgba(16,66,91,0.2)]"
          : "border-transparent bg-white/55 text-foreground/76 hover:border-border hover:bg-white/82 hover:text-foreground",
      )}
    >
      <span className={cn("flex h-9 w-9 items-center justify-center rounded-xl", isActive ? "bg-white/14" : "bg-primary/8 text-primary")}>{icon}</span>
      <span>{label}</span>
    </Link>
  );
}
