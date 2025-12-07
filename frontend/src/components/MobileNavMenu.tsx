"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
  const pathname = usePathname();

  const containerPosition =
    positionClassName || "fixed bottom-0 left-1/2 -translate-x-1/2 z-50";

  return (
    <div className={`${containerPosition} px-4 sm:px-0 ${className}`}>
      <nav
        className="flex items-center justify-between gap-6 rounded-full bg-white px-6 py-3 shadow-[0_10px_30px_rgba(0,0,0,0.15)] ring-1 ring-black/5 backdrop-blur-sm"
        aria-label="Primary navigation"
      >
        {items.map(({ key, label, href, Icon, badgeCount }) => {
          const isActive = activeKey
            ? key === activeKey
            : pathname === href || (href !== "/" && pathname?.startsWith(href));

          return (
            <Link
              key={key}
              href={href}
              className={`flex flex-col items-center justify-center transition-colors duration-200 ${
                isActive
                  ? "text-green-600"
                  : "text-gray-400 hover:text-green-600"
              }`}
            >
              <div className="relative">
                <Icon
                  size={24}
                  strokeWidth={isActive ? 2.0 : 1.5}
                  className="size-6"
                />

                {/* Badge thông báo */}
                {badgeCount !== undefined && badgeCount > 0 && (
                  <span className="absolute -right-1.5 -top-1.5 flex h-4 w-4 animate-in zoom-in items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white shadow-sm">
                    {badgeCount > 9 ? "9+" : badgeCount}
                  </span>
                )}
              </div>

              {/* Label nhỏ (10px) như footer mẫu */}
              <span
                className={`mt-1 text-[10px] leading-none ${
                  isActive ? "font-bold" : "font-medium"
                }`}
              >
                {label}
              </span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
