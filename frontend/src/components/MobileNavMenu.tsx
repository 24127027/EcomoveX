"use client";

import Link from "next/link";
import { LucideIcon } from "lucide-react";

export type MobileNavItem = {
  key: string;
  label: string;
  href: string;
  Icon: LucideIcon;
  badgeCount?: number;
};

interface MobileNavMenuProps {
  items: MobileNavItem[];
  activeKey?: string;
  className?: string;
  positionClassName?: string;
}

export function MobileNavMenu({
  items,
  activeKey,
  className = "",
  positionClassName,
}: MobileNavMenuProps) {
  const containerPosition =
    positionClassName ||
    "fixed bottom-6 left-1/2 -translate-x-1/2 sm:bottom-8 z-50";

  return (
    <div
      className={`${containerPosition} pointer-events-none px-4 sm:px-0 ${className}`}
    >
      <nav
        className="pointer-events-auto flex items-center gap-1 rounded-full bg-white/95 px-2 py-2 shadow-[0_18px_40px_rgba(15,118,110,0.25)] ring-1 ring-green-100 backdrop-blur"
        aria-label="Primary navigation"
      >
        {items.map(({ key, label, href, Icon, badgeCount }) => {
          const isActive = key === activeKey;

          return (
            <Link
              key={key}
              href={href}
              className={`flex flex-col items-center gap-1 rounded-2xl px-4 py-2 text-[11px] font-semibold transition-all duration-200 ${
                isActive
                  ? "bg-[#0F7E46] text-white shadow-lg"
                  : "text-gray-500 hover:text-green-600"
              }`}
            >
              <span
                className={`flex h-10 w-10 items-center justify-center rounded-full border transition-colors ${
                  isActive
                    ? "border-white/40 bg-white/10"
                    : "border-transparent bg-gray-100 text-gray-600"
                }`}
              >
                <Icon
                  size={isActive ? 20 : 18}
                  strokeWidth={isActive ? 2.5 : 2}
                  className={isActive ? "text-white" : "text-gray-600"}
                />
              </span>
              <span className="leading-none text-xs">
                {label}
                {badgeCount !== undefined && badgeCount > 0 && (
                  <span className="ml-1 rounded-full bg-red-500 px-1.5 py-0.5 text-[9px] font-black text-white">
                    {badgeCount > 9 ? "9+" : badgeCount}
                  </span>
                )}
              </span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
