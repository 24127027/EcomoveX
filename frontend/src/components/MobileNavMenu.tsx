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
    positionClassName || "fixed bottom-4 sm:bottom-6 left-1/2 -translate-x-1/2 z-50";

  return (
    <div className={`${containerPosition} px-4 sm:px-0 ${className}`}>
      <nav
        className="flex items-center justify-around gap-2 sm:gap-6 rounded-full bg-white/95 backdrop-blur-md px-3 sm:px-6 py-2.5 sm:py-3 shadow-[0_8px_24px_rgba(0,0,0,0.12)] sm:shadow-[0_10px_30px_rgba(0,0,0,0.15)] ring-1 ring-black/5 w-[calc(100vw-2rem)] sm:w-auto"
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
              className={`flex flex-col items-center justify-center min-w-[48px] transition-colors duration-200 ${
                isActive
                  ? "text-green-600"
                  : "text-gray-400 hover:text-green-600 active:text-green-500"
              }`}
            >
              <div className="relative">
                <Icon
                  size={22}
                  strokeWidth={isActive ? 2.0 : 1.5}
                  className="w-5 h-5 sm:w-6 sm:h-6"
                />

                {/* Badge thông báo */}
                {badgeCount !== undefined && badgeCount > 0 && (
                  <span className="absolute -right-1 -top-1 sm:-right-1.5 sm:-top-1.5 flex h-3.5 w-3.5 sm:h-4 sm:w-4 animate-in zoom-in items-center justify-center rounded-full bg-red-500 text-[8px] sm:text-[9px] font-bold text-white shadow-sm">
                    {badgeCount > 9 ? "9+" : badgeCount}
                  </span>
                )}
              </div>

              {/* Label nhỏ (10px) như footer mẫu */}
              <span
                className={`mt-0.5 sm:mt-1 text-[9px] sm:text-[10px] leading-none whitespace-nowrap ${
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
