"use client";

import Link from "next/link";
import { BarChart3, Plus, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type SessionSummaryProps = {
  cardsReviewed: number;
  sessionDurationMs: number;
  cardsRemaining: number;
  patternsDetected?: number;
  cardsGraduated?: number;
  cardsLapsed?: number;
  tomorrowDueCount?: number;
  tomorrowEstimatedMinutes?: number;
  onDismiss: () => void;
  onReviewAgain?: () => void;
  isLoadingStats?: boolean;
};

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes < 10) return `${minutes}m ${seconds}s`;
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remMinutes = minutes % 60;
  return `${hours}h ${remMinutes}m`;
}

export function SessionSummary({
  cardsReviewed,
  sessionDurationMs,
  cardsRemaining,
  patternsDetected = 0,
  cardsGraduated = 0,
  cardsLapsed = 0,
  tomorrowDueCount = 0,
  tomorrowEstimatedMinutes = 0,
  onDismiss,
  onReviewAgain,
  isLoadingStats = false,
}: SessionSummaryProps) {
  const durationDisplay = formatDuration(sessionDurationMs);
  const patternsLabel =
    patternsDetected === 1
      ? "1 new pattern detected"
      : `${patternsDetected} new patterns detected`;
  const tomorrowLabel =
    tomorrowDueCount === 1
      ? `Tomorrow: ~${tomorrowDueCount} card, ~${tomorrowEstimatedMinutes} min`
      : `Tomorrow: ~${tomorrowDueCount} cards, ~${tomorrowEstimatedMinutes} min`;

  return (
    <Card className="bg-zinc-100 border border-zinc-200 rounded-[14px]">
      <CardContent className="p-10 text-center">
        <h2 className="text-lg font-semibold text-text-primary">Session Complete</h2>
        <p className="mt-4 text-sm text-text-secondary">
          {cardsReviewed} cards reviewed in {durationDisplay}
        </p>
        {cardsRemaining > 0 ? (
          <p className="mt-1 text-sm text-text-muted">
            {cardsRemaining} cards remaining in queue
          </p>
        ) : null}
        <div className="mt-3 space-y-1">
          {isLoadingStats ? (
            <>
              <div className="mx-auto h-4 w-3/5 animate-pulse rounded bg-zinc-200" />
              <div className="mx-auto h-4 w-2/5 animate-pulse rounded bg-zinc-200" />
            </>
          ) : (
            <>
              {cardsGraduated > 0 ? (
                <p className="text-sm text-green-700">
                  {"\u2726"} {cardsGraduated} {cardsGraduated === 1 ? "card" : "cards"} graduated to mastered
                </p>
              ) : null}
              {patternsDetected > 0 ? (
                <p className="text-sm text-blue-600">
                  {"\u2726"}{" "}
                  <Link href="/dashboard" onClick={onDismiss} className="underline underline-offset-4">
                    {patternsLabel}
                  </Link>
                </p>
              ) : null}
              <p className="text-sm text-zinc-600">{"\u2726"} {tomorrowLabel}</p>
            </>
          )}
        </div>
        <div className="mt-6 flex items-center justify-center gap-3 flex-wrap">
          {!isLoadingStats && cardsLapsed > 0 && onReviewAgain ? (
            <Button variant="outline" onClick={onReviewAgain}>
              <RotateCcw className="mr-2 size-4" />
              Review Again
            </Button>
          ) : null}
          <Button asChild variant="primary">
            <Link href="/dashboard" onClick={onDismiss}>
              <BarChart3 className="mr-2 size-4" />
              View Dashboard
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/vocabulary" onClick={onDismiss}>
              <Plus className="mr-2 size-4" />
              Add Words
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}