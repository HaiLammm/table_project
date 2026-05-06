"use client";

import type { RatingValue } from "@/types/srs";

type RatingButtonVariant = "again" | "hard" | "good" | "easy";

const VARIANT_CONFIG: Record<
  RatingButtonVariant,
  {
    number: RatingValue;
    label: string;
    hoverClass: string;
    flashClass: string;
  }
> = {
  again: {
    number: 1,
    label: "Again",
    hoverClass: "hover:bg-red-50 hover:border-red-200 hover:text-red-700",
    flashClass: "border-red-300",
  },
  hard: {
    number: 2,
    label: "Hard",
    hoverClass: "hover:bg-amber-50 hover:border-amber-200 hover:text-amber-700",
    flashClass: "border-amber-300",
  },
  good: {
    number: 3,
    label: "Good",
    hoverClass: "hover:bg-green-50 hover:border-green-200 hover:text-green-700",
    flashClass: "border-green-300",
  },
  easy: {
    number: 4,
    label: "Easy",
    hoverClass: "hover:bg-zinc-100 hover:border-zinc-300 hover:text-zinc-900",
    flashClass: "border-zinc-400",
  },
};

type RatingButtonProps = {
  variant: RatingButtonVariant;
  interval: string;
  onRate: () => void;
  disabled?: boolean;
};

export function RatingButton({ variant, interval, onRate, disabled = false }: RatingButtonProps) {
  const config = VARIANT_CONFIG[variant];

  return (
    <button
      type="button"
      disabled={disabled}
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
      `}
    >
      <span className="absolute top-1 right-1.5 rounded bg-zinc-100 px-1.5 py-px text-[10px] font-semibold text-zinc-500 leading-none">
        {config.number}
      </span>

      <span className="text-sm font-medium">{config.label}</span>

      <span className="mt-0.5 text-[11px] text-zinc-400 leading-none">{interval}</span>
    </button>
  );
}
