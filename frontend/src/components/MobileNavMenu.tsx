"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X, LucideIcon, ChevronRight } from "lucide-react";

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
  buttonLabel?: string;
  variant?: "floating" | "flat";
  positionClassName?: string;
}

export function MobileNavMenu({
  items,
  activeKey,
  className = "",
  buttonLabel = "Menu",
  variant = "floating",
  positionClassName,
}: MobileNavMenuProps) {
  const [open, setOpen] = useState(false);

  const baseButtonClasses =
    "flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition-colors";
  const floatingStyles =
    "bg-white/95 text-gray-700 shadow-lg ring-1 ring-black/5 backdrop-blur hover:text-green-600";
  const flatStyles =
    "bg-white text-gray-600 border border-gray-200 shadow-sm hover:border-green-400 hover:text-green-600";
  const containerPosition = positionClassName || "fixed top-4 left-4";

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-[40] bg-black/30 backdrop-blur-[1px]"
          onClick={() => setOpen(false)}
        />
      )}

      <div className={`${containerPosition} z-[60] ${className}`}>
        <div className="relative">
          <button
            onClick={() => setOpen((prev) => !prev)}
            className={`${baseButtonClasses} ${
              variant === "flat" ? flatStyles : floatingStyles
            }`}
            aria-expanded={open}
            aria-label="Open navigation menu"
          >
            {open ? <X size={18} /> : <Menu size={18} />}
            <span>{buttonLabel}</span>
          </button>

          {open && (
            <div className="absolute left-0 right-auto mt-3 w-64 origin-top-left rounded-2xl border border-gray-100 bg-white p-2 text-gray-700 shadow-2xl">
              <div className="px-2 pb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Quick navigation
              </div>
              <div className="flex flex-col gap-1">
                {items.map(({ key, label, href, Icon, badgeCount }) => {
                  const isActive = key === activeKey;
                  return (
                    <Link
                      key={key}
                      href={href}
                      onClick={() => setOpen(false)}
                      className={`flex items-center justify-between rounded-xl px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? "bg-green-50 text-green-700 border border-green-100"
                          : "hover:bg-gray-50"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`flex h-8 w-8 items-center justify-center rounded-full border ${
                            isActive
                              ? "border-green-200 bg-white text-green-600"
                              : "border-gray-200 bg-gray-50 text-gray-500"
                          }`}
                        >
                          <Icon size={18} strokeWidth={2} />
                        </span>
                        <div className="flex flex-col leading-tight">
                          <span className="font-semibold">{label}</span>
                          <span className="text-[11px] text-gray-400">
                            Tap to open
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {badgeCount !== undefined && badgeCount > 0 && (
                          <span className="rounded-full bg-red-500 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                            {badgeCount > 9 ? "9+" : badgeCount}
                          </span>
                        )}
                        <ChevronRight
                          size={16}
                          className={
                            isActive ? "text-green-500" : "text-gray-400"
                          }
                        />
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
