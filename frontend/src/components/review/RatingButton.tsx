"use client";

import type { RatingValue } from "@/types/srs";

type RatingButtonVariant = "again" | "hard" | "good" | "easy";

const VARIANT_CONFIG: Record<
  RatingButtonVariant,
  {
    number: RatingValue;
    label: string;
    hoverClass: string;
  }
> = {
  again: {
    number: 1,
    label: "Again",
    hoverClass: "hover:bg-red-50 hover:border-red-200 hover:text-red-700",
  },
  hard: {
    number: 2,
    label: "Hard",
    hoverClass: "hover:bg-amber-50 hover:border-amber-200 hover:text-amber-700",
  },
  good: {
    number: 3,
    label: "Good",
    hoverClass: "hover:bg-green-50 hover:border-green-200 hover:text-green-700",
  },
  easy: {
    number: 4,
    label: "Easy",
    hoverClass: "hover:bg-zinc-100 hover:border-zinc-300 hover:text-zinc-900",
  },
};

type RatingButtonProps = {
  variant: RatingButtonVariant;
  interval: string;
  onRate: () => void;
  disabled?: boolean;
  isLoading?: boolean;
};

export function RatingButton({ variant, interval, onRate, disabled = false, isLoading = false }: RatingButtonProps) {
  const config = VARIANT_CONFIG[variant];

  return (
    <button
      type="button"
      disabled={disabled || isLoading}
      onClick={onRate}
      aria-label={`Rate as ${config.label}, next review in ${interval}`}
      className={`
        relative flex flex-col items-center justify-center min-h-[48px] min-w-[48px] w-full
        bg-white border border-zinc-200 rounded-[10px] py-2.5 px-2
        text-center text-sm font-medium text-zinc-700
        transition-colors duration-150
        active:scale-[0.97]
        disabled:opacity-40 disabled:cursor-not-allowed
        ${config.hoverClass}
        ${isLoading ? "opacity-60" : ""}
      `}
    >
      {isLoading ? (
        <svg className="absolute top-1 right-1.5 size-3.5 animate-spin text-zinc-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      ) : (
        <span className="absolute top-1 right-1.5 rounded bg-zinc-100 px-1.5 py-px text-[10px] font-semibold text-zinc-500 leading-none">
          {config.number}
        </span>
      )}

      <span className="text-sm font-medium">{config.label}</span>

      <span className="mt-0.5 text-[11px] text-zinc-400 leading-none">{interval}</span>
    </button>
  );
}
