"use client";

import { Menu, Search } from "lucide-react";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";

type TopbarProps = {
  mobileOpen: boolean;
  onMenuToggle: () => void;
};

const pageLabels: Record<string, string> = {
  "/": "Today's Queue",
  "/collections": "Collections",
  "/dashboard": "Dashboard",
  "/settings": "Settings",
};

function getCurrentPageLabel(pathname: string) {
  if (pathname === "/") {
    return pageLabels[pathname];
  }

  const [segment] = pathname.split("/").filter(Boolean);

  return pageLabels[`/${segment}`] ?? "Current Page";
}

export function Topbar({ mobileOpen, onMenuToggle }: TopbarProps) {
  const pathname = usePathname();
  const currentPage = getCurrentPageLabel(pathname);

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center border-b border-[var(--chrome-border)] bg-[var(--chrome-bg)] px-4 sm:px-6 lg:px-8">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          onClick={onMenuToggle}
          aria-label="Open navigation menu"
          aria-expanded={mobileOpen}
          className="border border-zinc-800 bg-transparent text-zinc-200 hover:bg-zinc-800 hover:text-zinc-50 sm:hidden"
        >
          <Menu className="size-5" />
        </Button>

        <div className="min-w-0 overflow-hidden whitespace-nowrap text-sm">
          <span className="text-zinc-500">TableProject</span>
          <span className="px-2 text-zinc-600">/</span>
          <span className="inline-block max-w-full truncate align-bottom font-medium text-zinc-200">
            {currentPage}
          </span>
        </div>
      </div>

      <div className="ml-4 flex items-center gap-2 sm:gap-3">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled
          className="gap-2 border border-zinc-800 bg-zinc-900/50 px-3 text-zinc-200 opacity-100 hover:bg-zinc-800 hover:text-zinc-50 disabled:opacity-100"
        >
          <Search className="size-4" />
          <span className="hidden sm:inline">Search</span>
          <kbd className="hidden rounded-md border border-zinc-700 bg-zinc-800 px-1.5 py-0.5 font-mono text-[11px] text-zinc-300 sm:inline-flex">
            ⌘K
          </kbd>
        </Button>

        <div
          aria-hidden="true"
          className="size-8 rounded-full border border-zinc-600 bg-zinc-700"
        />
      </div>
    </header>
  );
}
