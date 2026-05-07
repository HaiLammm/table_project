"use client";

import Link from "next/link";
import {
  AlertTriangle,
  BrainCircuit,
  CalendarRange,
  Clock3,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import type { ComponentType, SVGProps } from "react";
import type { InsightSeverity } from "@/types/diagnostics";

type IconComponent = ComponentType<SVGProps<SVGSVGElement>>;

export interface InsightCardProps {
  icon: string;
  label: string;
  title: string;
  text: string;
  variant: "inline" | "expandable";
  severity: InsightSeverity;
  expandedContent?: string;
  actionLabel?: string;
  actionHref?: string;
  onDismiss?: () => void;
}

const ICONS: Record<string, IconComponent> = {
  clock: Clock3,
  "alert-triangle": AlertTriangle,
  "trending-up": TrendingUp,
  sparkles: Sparkles,
  brain: BrainCircuit,
  calendar: CalendarRange,
  zap: Zap,
};

const SEVERITY_ICON_CLASSES: Record<InsightSeverity, string> = {
  info: "text-blue-400",
  warning: "text-amber-400",
  success: "text-green-400",
};

export function InsightCard({
  icon,
  label,
  title,
  text,
  variant,
  severity,
  expandedContent,
  actionLabel,
  actionHref,
  onDismiss,
}: InsightCardProps) {
  const Icon = ICONS[icon] ?? Sparkles;

  return (
    <aside
      role="complementary"
      aria-label="Learning insight"
      className="bg-zinc-900 border border-zinc-800 rounded-[10px] p-4"
    >
      <div className="flex items-start gap-3">
        <div className={SEVERITY_ICON_CLASSES[severity]}>
          <Icon className="size-5" aria-hidden="true" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">{label}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-100">{title}</p>
          <p className="mt-2 text-sm leading-relaxed text-zinc-400">{text}</p>

          {variant === "expandable" && expandedContent ? (
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">{expandedContent}</p>
          ) : null}

          {actionLabel && actionHref ? (
            <Link
              href={actionHref}
              className="mt-3 inline-flex text-sm text-zinc-300 underline underline-offset-4 hover:text-zinc-100"
            >
              {actionLabel}
            </Link>
          ) : null}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3 border-t border-zinc-800 pt-3">
        <p className="text-xs text-zinc-500">Press Space to continue</p>

        {onDismiss ? (
          <button
            type="button"
            onClick={onDismiss}
            className="text-xs text-zinc-500 underline underline-offset-4 hover:text-zinc-300"
          >
            Dismiss
          </button>
        ) : null}
      </div>
    </aside>
  );
}
