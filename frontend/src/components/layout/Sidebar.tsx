"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  CalendarCheck,
  FolderOpen,
  type LucideIcon,
  Settings,
} from "lucide-react";

import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";

type SidebarProps = {
  mobileOpen: boolean;
  onMobileOpenChange: (open: boolean) => void;
};

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  badge?: number;
};

const navItems: NavItem[] = [
  {
    href: "/",
    label: "Today's Queue",
    icon: CalendarCheck,
  },
  {
    href: "/collections",
    label: "Collections",
    icon: FolderOpen,
  },
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: BarChart3,
  },
  {
    href: "/settings",
    label: "Settings",
    icon: Settings,
  },
] as const;

function isActivePath(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar({ mobileOpen, onMobileOpenChange }: SidebarProps) {
  const pathname = usePathname();
  const reviewInProgress = useUIStore((s) => s.reviewInProgress);

  return (
    <>
      <aside
        className={cn(
          "sticky top-0 hidden h-screen shrink-0 border-r border-[var(--chrome-border)] bg-[var(--chrome-bg)] text-[var(--chrome-text)] transition-[width] duration-200 sm:flex",
          reviewInProgress
            ? "w-[var(--sidebar-collapsed-width)] lg:w-[56px]"
            : "w-[var(--sidebar-collapsed-width)] lg:w-[var(--sidebar-width)]",
        )}
      >
        <div className="flex w-full flex-col">
          <div className="flex h-14 items-center border-b border-[var(--chrome-border)] px-4 text-sm font-semibold tracking-tight text-zinc-50 sm:justify-center lg:justify-start">
            <span className={cn("hidden lg:inline", reviewInProgress && "lg:hidden")}>TableProject</span>
            <span className={cn("lg:hidden", reviewInProgress && "lg:inline")}>TP</span>
          </div>

          <nav aria-label="Main navigation" className="flex flex-1 flex-col gap-1 p-2">
            {navItems.map((item) => {
              const active = isActivePath(pathname, item.href);
              const Icon = item.icon;

              return (
                <Tooltip key={item.href}>
                  <TooltipTrigger asChild>
                    <Link
                      href={item.href}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "flex items-center justify-center rounded-lg py-2 text-sm transition-colors focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-900 sm:px-0 lg:justify-start lg:px-3",
                        active
                          ? "bg-zinc-800 font-medium text-zinc-50"
                          : "text-[var(--chrome-text)] hover:bg-zinc-800/50 hover:text-zinc-200",
                      )}
                    >
                      <Icon className="size-5 shrink-0" />
                      <span className={cn("ml-3 hidden lg:inline", reviewInProgress && "lg:hidden")}>
                        {item.label}
                      </span>
                      {typeof item.badge === "number" ? (
                        <span
                          className={cn(
                            "ml-auto hidden rounded-full bg-zinc-700 px-2 text-xs font-semibold text-zinc-50 lg:inline-flex",
                            reviewInProgress && "lg:hidden",
                          )}
                        >
                          {item.badge}
                        </span>
                      ) : null}
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent side="right" sideOffset={12} className="hidden sm:flex lg:hidden">
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </nav>
        </div>
      </aside>

      <Sheet open={mobileOpen} onOpenChange={onMobileOpenChange}>
        <SheetContent
          side="left"
          aria-describedby={undefined}
          className="w-[240px] border-[var(--chrome-border)] bg-[var(--chrome-bg)] p-0 text-[var(--chrome-text)] sm:hidden"
        >
          <SheetTitle className="sr-only">Main navigation</SheetTitle>

          <div className="flex h-full flex-col">
            <div className="flex h-14 items-center border-b border-[var(--chrome-border)] px-4 text-sm font-semibold tracking-tight text-zinc-50">
              TableProject
            </div>

            <nav aria-label="Main navigation" className="flex flex-1 flex-col gap-1 p-2 pr-12">
              {navItems.map((item) => {
                const active = isActivePath(pathname, item.href);
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    onClick={() => onMobileOpenChange(false)}
                    className={cn(
                      "flex items-center rounded-lg px-3 py-2 text-sm transition-colors focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-900",
                      active
                        ? "bg-zinc-800 font-medium text-zinc-50"
                        : "text-[var(--chrome-text)] hover:bg-zinc-800/50 hover:text-zinc-200",
                    )}
                  >
                    <Icon className="size-5 shrink-0" />
                    <span className="ml-3">{item.label}</span>
                    {typeof item.badge === "number" ? (
                      <span className="ml-auto rounded-full bg-zinc-700 px-2 text-xs font-semibold text-zinc-50">
                        {item.badge}
                      </span>
                    ) : null}
                  </Link>
                );
              })}
            </nav>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
