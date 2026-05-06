"use client";

import { useCallback, useEffect } from "react";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { CatchUpBanner, QueueHeader, ReviewCard } from "@/components/review";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { useDueCards } from "@/hooks/useDueCards";
import { useQueueStats } from "@/hooks/useQueueStats";
import { useRatingMutation } from "@/hooks/useRatingMutation";
import { useReviewKeyboard } from "@/hooks/useReviewKeyboard";
import { useReviewStore } from "@/stores/review-store";
import type { RatingValue } from "@/types/srs";

const EXAMPLE_INTERVALS: Record<string, string> = {
  again: "<1m",
  hard: "6m",
  good: "1d",
  easy: "4d",
};

export default function ReviewPage() {
  const queueMode = useReviewStore((s) => s.queueMode);
  const setQueueMode = useReviewStore((s) => s.setQueueMode);
  const currentCardIndex = useReviewStore((s) => s.currentCardIndex);
  const isRevealed = useReviewStore((s) => s.isRevealed);
  const showJpDefinition = useReviewStore((s) => s.showJpDefinition);
  const sessionCards = useReviewStore((s) => s.sessionCards);
  const setSessionCards = useReviewStore((s) => s.setSessionCards);
  const resetSession = useReviewStore((s) => s.resetSession);
  const isRatingInProgress = useReviewStore((s) => s.isRatingInProgress);
  const revealedAt = useReviewStore((s) => s.revealedAt);
  const lastRating = useReviewStore((s) => s.lastRating);
  const activeRating = useReviewStore((s) => s.activeRating);
  const setRatingInProgress = useReviewStore((s) => s.setRatingInProgress);
  const setLastRating = useReviewStore((s) => s.setLastRating);
  const setActiveRating = useReviewStore((s) => s.setActiveRating);
  const setRevealedAt = useReviewStore((s) => s.setRevealedAt);
  const nextCard = useReviewStore((s) => s.nextCard);

  const toast = useToast();
  const { mutateAsync: rateCardMutate } = useRatingMutation(queueMode);

  const queueStatsQuery = useQueueStats();
  const dueCount = queueStatsQuery.data?.due_count ?? 0;

  const { sessionCards: fetchedCards, isLoading: cardsLoading } = useDueCards(
    queueMode,
    queueStatsQuery.isSuccess && dueCount > 0,
  );

  useEffect(() => {
    if (fetchedCards.length > 0) {
      setSessionCards(fetchedCards);
    }
  }, [fetchedCards, setSessionCards]);

  useEffect(() => {
    return () => {
      resetSession();
    };
  }, [resetSession]);

  const handleRate = useCallback(
    async (rating: RatingValue) => {
      if (isRatingInProgress) return;

      const currentCard = sessionCards[currentCardIndex];
      if (!currentCard) return;

      const responseTimeMs = revealedAt != null ? Date.now() - revealedAt : null;

      setRatingInProgress(true);
      setLastRating(rating);
      setActiveRating(rating);

      try {
        await rateCardMutate({
          cardId: currentCard.id,
          data: {
            rating,
            response_time_ms: responseTimeMs,
          },
        });
        nextCard();
      } catch (error) {
        const apiError = error as { status?: number };
        if (apiError.status === 422) {
          if (process.env.NODE_ENV === "development") {
            console.warn("[Review] Card not due, skipping to next card");
          }
          nextCard();
          return;
        }
        toast.error("Failed to save rating. Please try again.");
        setRatingInProgress(false);
        setLastRating(null);
        setActiveRating(null);
        setRevealedAt(Date.now());
      }
    },
    [
      isRatingInProgress,
      sessionCards,
      currentCardIndex,
      revealedAt,
      setRatingInProgress,
      setLastRating,
      setActiveRating,
      setRevealedAt,
      rateCardMutate,
      nextCard,
      toast,
    ],
  );

  useReviewKeyboard(handleRate);

  if (queueStatsQuery.isLoading) {
    return (
      <section className="mx-auto flex min-h-[60vh] w-full max-w-[720px] flex-col justify-center gap-4 px-4 py-6 sm:px-6 lg:px-0">
        <Card>
          <CardContent className="space-y-3 py-6">
            <div className="h-6 w-48 animate-pulse rounded-full bg-muted" />
            <div className="h-4 w-64 animate-pulse rounded-full bg-muted" />
          </CardContent>
        </Card>
        <div className="h-80 animate-pulse rounded-[14px] bg-zinc-100" />
      </section>
    );
  }

  if (queueStatsQuery.isError || queueStatsQuery.data === undefined) {
    return (
      <section className="mx-auto flex min-h-[60vh] w-full max-w-[720px] items-center px-4 py-6 sm:px-6 lg:px-0">
        <Card className="w-full">
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <p className="text-sm font-medium text-text-primary">
              Unable to load review queue
            </p>
            <p className="text-sm text-text-secondary">
              We couldn&apos;t fetch your current review queue. Please refresh and try again.
            </p>
          </CardContent>
        </Card>
      </section>
    );
  }

  if (dueCount === 0) {
    return (
      <section className="mx-auto flex min-h-[70vh] w-full max-w-[720px] flex-col items-center justify-center px-4 py-6 text-center sm:px-6 lg:px-0">
        <CheckCircle2 className="size-10 text-zinc-400" />
        <h1 className="mt-5 text-lg font-semibold text-text-primary">All caught up!</h1>
        <p className="mt-2 max-w-md text-sm text-text-secondary">
          No cards due for review. Come back tomorrow or add new words to your collection.
        </p>
        <Button asChild className="mt-6">
          <Link href="/vocabulary">Add Words</Link>
        </Button>
      </section>
    );
  }

  const currentCard = sessionCards[currentCardIndex];

  return (
    <section className="mx-auto flex w-full max-w-[720px] flex-col gap-4 px-4 py-6 sm:px-6 lg:px-0">
      <Card>
        <CardContent className="py-6">
          <QueueHeader
            dueCount={queueStatsQuery.data.due_count}
            estimatedMinutes={queueStatsQuery.data.estimated_minutes}
            retentionRate={queueStatsQuery.data.retention_rate}
          />
        </CardContent>
      </Card>

      {queueStatsQuery.data.overdue_count >= 100 ? (
        <CatchUpBanner
          overdueCount={queueStatsQuery.data.overdue_count}
          queueMode={queueMode}
          onStartCatchUp={() => setQueueMode("catchup")}
          onReviewAll={() => setQueueMode("full")}
        />
      ) : null}

      {cardsLoading || !currentCard ? (
        <Card>
          <CardContent className="space-y-3 py-10">
            <div className="mx-auto h-8 w-48 animate-pulse rounded-full bg-muted" />
            <div className="mx-auto h-5 w-64 animate-pulse rounded-full bg-muted" />
            <div className="mx-auto h-4 w-36 animate-pulse rounded-full bg-muted" />
          </CardContent>
        </Card>
      ) : (
        <ReviewCard
          card={currentCard}
          currentIndex={currentCardIndex}
          totalCards={sessionCards.length}
          isRevealed={isRevealed}
          showJpDefinition={showJpDefinition}
          onRate={handleRate}
          isRatingInProgress={isRatingInProgress}
          lastRating={lastRating}
          activeRating={activeRating}
          intervals={EXAMPLE_INTERVALS}
        />
      )}
    </section>
  );
}
