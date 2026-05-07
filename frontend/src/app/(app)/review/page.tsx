"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { CatchUpBanner, InsightCard, QueueHeader, ReviewCard, SessionSummary } from "@/components/review";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { useDueCards } from "@/hooks/useDueCards";
import { useInsightSeenMutation } from "@/hooks/useInsightSeenMutation";
import { usePendingInsights } from "@/hooks/usePendingInsights";
import { useQueueStats } from "@/hooks/useQueueStats";
import { useRatingMutation } from "@/hooks/useRatingMutation";
import { useReviewKeyboard } from "@/hooks/useReviewKeyboard";
import { useSessionStats } from "@/hooks/useSessionStats";
import { useUndoMutation } from "@/hooks/useUndoMutation";
import { useReviewStore } from "@/stores/review-store";
import { useUIStore } from "@/stores/ui-store";
import type { RatingValue } from "@/types/srs";

const EXAMPLE_INTERVALS: Record<string, string> = {
  again: "<1m",
  hard: "6m",
  good: "1d",
  easy: "4d",
};

const SESSION_PROGRESS_KEY = "review_session_progress";

type SavedSessionProgress = {
  cardIds: number[];
  currentIndex: number;
  sessionStartedAt: number | null;
  diagnosticsSessionId?: string | null;
};

const RATING_LABELS: Record<number, string> = {
  1: "Again",
  2: "Hard",
  3: "Good",
  4: "Easy",
};

function createDiagnosticsSessionId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `session-${Date.now()}`;
}

function saveSessionProgress(
  cardIds: number[],
  currentIndex: number,
  sessionStartedAt: number | null,
  diagnosticsSessionId: string | null,
) {
  try {
    localStorage.setItem(
      SESSION_PROGRESS_KEY,
      JSON.stringify({ cardIds, currentIndex, sessionStartedAt, diagnosticsSessionId }),
    );
  } catch {
    // localStorage not available
  }
}

function loadSessionProgress(): SavedSessionProgress | null {
  try {
    const raw = localStorage.getItem(SESSION_PROGRESS_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SavedSessionProgress;
  } catch {
    return null;
  }
}

function clearSessionProgress() {
  try {
    localStorage.removeItem(SESSION_PROGRESS_KEY);
  } catch {
    // localStorage not available
  }
}

export default function ReviewPage() {
  const queueMode = useReviewStore((s) => s.queueMode);
  const setQueueMode = useReviewStore((s) => s.setQueueMode);
  const currentCardIndex = useReviewStore((s) => s.currentCardIndex);
  const isRevealed = useReviewStore((s) => s.isRevealed);
  const showJpDefinition = useReviewStore((s) => s.showJpDefinition);
  const sessionCards = useReviewStore((s) => s.sessionCards);
  const isRatingInProgress = useReviewStore((s) => s.isRatingInProgress);
  const revealedAt = useReviewStore((s) => s.revealedAt);
  const lastRating = useReviewStore((s) => s.lastRating);
  const activeRating = useReviewStore((s) => s.activeRating);
  const currentInsight = useReviewStore((s) => s.currentInsight);
  const isShowingInsight = useReviewStore((s) => s.isShowingInsight);
  const insightsSeen = useReviewStore((s) => s.insightsSeen);
  const setRatingInProgress = useReviewStore((s) => s.setRatingInProgress);
  const setLastRating = useReviewStore((s) => s.setLastRating);
  const setActiveRating = useReviewStore((s) => s.setActiveRating);
  const setRevealedAt = useReviewStore((s) => s.setRevealedAt);
  const setPendingInsights = useReviewStore((s) => s.setPendingInsights);
  const nextCard = useReviewStore((s) => s.nextCard);
  const showNextInsight = useReviewStore((s) => s.showNextInsight);
  const dismissInsight = useReviewStore((s) => s.dismissInsight);

  const rateCardAction = useReviewStore((s) => s.rateCardAction);
  const undoLastRating = useReviewStore((s) => s.undoLastRating);
  const startSession = useReviewStore((s) => s.startSession);
  const incrementCardsReviewed = useReviewStore((s) => s.incrementCardsReviewed);
  const endSession = useReviewStore((s) => s.endSession);
  const dismissSessionSummary = useReviewStore((s) => s.dismissSessionSummary);
  const showSessionSummary = useReviewStore((s) => s.showSessionSummary);
  const sessionStartedAt = useReviewStore((s) => s.sessionStartedAt);
  const sessionCompletedAt = useReviewStore((s) => s.sessionCompletedAt);
  const cardsReviewed = useReviewStore((s) => s.cardsReviewed);
  const lastRatedCardId = useReviewStore((s) => s.lastRatedCardId);
  const undoAvailableUntil = useReviewStore((s) => s.undoAvailableUntil);

  const setReviewInProgress = useUIStore((s) => s.setReviewInProgress);

  const toast = useToast();
  const { mutateAsync: rateCardMutate } = useRatingMutation(queueMode);
  const { mutateAsync: undoMutate } = useUndoMutation(queueMode);
  const { mutate: markInsightSeen } = useInsightSeenMutation();

  const undoToastIdRef = useRef<number | null>(null);
  const undoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastWriteRef = useRef(0);
  const [diagnosticsSessionId, setDiagnosticsSessionId] = useState<string | null>(null);

  const queueStatsQuery = useQueueStats();
  const dueCount = queueStatsQuery.data?.due_count ?? 0;

  const { sessionCards: fetchedCards, isLoading: cardsLoading } = useDueCards(
    queueMode,
    queueStatsQuery.isSuccess && dueCount > 0,
  );
  const pendingInsightsQuery = usePendingInsights(
    diagnosticsSessionId,
    queueStatsQuery.isSuccess && dueCount > 0,
  );
  const sessionStatsQuery = useSessionStats(
    diagnosticsSessionId,
    showSessionSummary && diagnosticsSessionId !== null,
  );

  useEffect(() => {
    setReviewInProgress(true);
    return () => {
      setReviewInProgress(false);
    };
  }, [setReviewInProgress]);

  useEffect(() => {
    if (fetchedCards.length === 0) return;

    const saved = loadSessionProgress();
    if (saved && saved.cardIds.length > 0) {
      const matchCount = Math.min(fetchedCards.length, saved.cardIds.length);
      let allMatch = true;
      for (let i = 0; i < matchCount; i++) {
        if (fetchedCards[i].id !== saved.cardIds[i]) {
          allMatch = false;
          break;
        }
      }

      if (allMatch && saved.cardIds.length === fetchedCards.length) {
        const resumedSessionId = saved.diagnosticsSessionId ?? createDiagnosticsSessionId();
        queueMicrotask(() => setDiagnosticsSessionId(resumedSessionId));
        startSession(fetchedCards);
        useReviewStore.setState({
          currentCardIndex: saved.currentIndex,
          cardsReviewed: saved.currentIndex,
          previousCardIndex: saved.currentIndex > 0 ? saved.currentIndex - 1 : null,
        });
        if (saved.sessionStartedAt) {
          useReviewStore.setState({ sessionStartedAt: saved.sessionStartedAt });
        }
        clearSessionProgress();
        return;
      }
    }

    const nextSessionId = createDiagnosticsSessionId();
    queueMicrotask(() => setDiagnosticsSessionId(nextSessionId));
    startSession(fetchedCards);
    clearSessionProgress();
  }, [fetchedCards, startSession]);

  useEffect(() => {
    if (!pendingInsightsQuery.isSuccess) return;
    setPendingInsights(pendingInsightsQuery.data.items);
  }, [pendingInsightsQuery.isSuccess, pendingInsightsQuery.data, setPendingInsights]);

  const debouncedSaveProgress = useCallback(() => {
    const state = useReviewStore.getState();
    const cardIds = state.sessionCards.map((c) => c.id);
    const now = Date.now();
    if (now - lastWriteRef.current < 500) return;
    lastWriteRef.current = now;
    saveSessionProgress(
      cardIds,
      state.currentCardIndex,
      state.sessionStartedAt,
      diagnosticsSessionId,
    );
  }, [diagnosticsSessionId]);

  const handleEndSession = useCallback(() => {
    if (sessionCards.length === 0) return;
    setReviewInProgress(false);
    endSession();
    clearSessionProgress();

    if (undoToastIdRef.current !== null) {
      toast.dismissToast(undoToastIdRef.current);
      undoToastIdRef.current = null;
    }
    if (undoTimerRef.current !== null) {
      clearTimeout(undoTimerRef.current);
      undoTimerRef.current = null;
    }
  }, [sessionCards.length, endSession, setReviewInProgress, toast]);

  const handleUndo = useCallback(async () => {
    if (lastRatedCardId === null) return;
    if (undoAvailableUntil !== null && Date.now() >= undoAvailableUntil) return;

    if (undoTimerRef.current !== null) {
      clearTimeout(undoTimerRef.current);
      undoTimerRef.current = null;
    }

    try {
      await undoMutate({ cardId: lastRatedCardId });
      undoLastRating();
      saveSessionProgress(
        useReviewStore.getState().sessionCards.map((c) => c.id),
        useReviewStore.getState().previousCardIndex ?? 0,
        useReviewStore.getState().sessionStartedAt,
        diagnosticsSessionId,
      );

      if (undoToastIdRef.current !== null) {
        toast.dismissToast(undoToastIdRef.current);
        undoToastIdRef.current = null;
      }
      if (undoTimerRef.current !== null) {
        clearTimeout(undoTimerRef.current);
        undoTimerRef.current = null;
      }
    } catch {
      toast.error("Unable to undo rating");
    }
  }, [diagnosticsSessionId, lastRatedCardId, undoAvailableUntil, undoMutate, undoLastRating, toast]);

  const handleDismissInsight = useCallback(() => {
    const insightToMark = useReviewStore.getState().currentInsight;
    dismissInsight();

    if (!insightToMark || !diagnosticsSessionId) return;

    markInsightSeen(
      {
        insightId: insightToMark.id,
        sessionId: diagnosticsSessionId,
      },
      {
        onError: () => {
          toast.error("Unable to save insight state");
        },
      },
    );
  }, [diagnosticsSessionId, dismissInsight, markInsightSeen, toast]);

  const handleReviewAgain = useCallback(() => {
    const lapsedCardIds = sessionStatsQuery.data?.lapsed_card_ids;
    if (!lapsedCardIds || lapsedCardIds.length === 0) return;

    const lapsedSet = new Set(lapsedCardIds);
    const filteredCards = sessionCards.filter((card) => lapsedSet.has(card.id));

    if (filteredCards.length === 0) return;

    const newSessionId = createDiagnosticsSessionId();
    setDiagnosticsSessionId(newSessionId);
    clearSessionProgress();
    startSession(filteredCards);
    setReviewInProgress(true);
  }, [sessionStatsQuery.data, sessionCards, startSession, setReviewInProgress]);

  const handleRate = useCallback(
    async (rating: RatingValue) => {
      if (isRatingInProgress) return;

      const currentCard = sessionCards[currentCardIndex];
      if (!currentCard) return;

      const responseTimeMs = revealedAt != null ? Date.now() - revealedAt : null;

      setRatingInProgress(true);
      setLastRating(rating);
      setActiveRating(rating);

      const label = RATING_LABELS[rating] ?? String(rating);
      rateCardAction(rating, currentCard.id, label);

      try {
        await rateCardMutate({
          cardId: currentCard.id,
          data: {
            rating,
            response_time_ms: responseTimeMs,
            session_id: diagnosticsSessionId,
          },
        });

        incrementCardsReviewed();

        undoToastIdRef.current = toast.showUndoToast({
          message: `Card rated ${label} — Ctrl+Z to undo`,
          action: {
            label: "Undo",
            onClick: handleUndo,
          },
        });

        undoTimerRef.current = setTimeout(() => {
          useReviewStore.getState().undoAvailableUntil = null;
          useReviewStore.getState().lastRatedCardId = null;
          useReviewStore.getState().ratingLabelForUndo = null;
          if (undoToastIdRef.current !== null) {
            toast.dismissToast(undoToastIdRef.current);
            undoToastIdRef.current = null;
          }
          undoTimerRef.current = null;
        }, 3000);

        nextCard();
        showNextInsight();
        debouncedSaveProgress();
      } catch (error) {
        const apiError = error as { status?: number };
        if (apiError.status === 422) {
          if (process.env.NODE_ENV === "development") {
            console.warn("[Review] Card not due, skipping to next card");
          }
          nextCard();
          showNextInsight();
          debouncedSaveProgress();
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
      showNextInsight,
      toast,
      rateCardAction,
      incrementCardsReviewed,
      handleUndo,
      debouncedSaveProgress,
      diagnosticsSessionId,
    ],
  );

  useReviewKeyboard(handleRate, handleEndSession, handleUndo, handleDismissInsight);

  useEffect(() => {
    if (
      sessionCards.length > 0 &&
      currentCardIndex >= sessionCards.length &&
      !showSessionSummary &&
      !isShowingInsight
    ) {
      setReviewInProgress(false);
      endSession();
      clearSessionProgress();

      if (undoToastIdRef.current !== null) {
        toast.dismissToast(undoToastIdRef.current);
        undoToastIdRef.current = null;
      }
      if (undoTimerRef.current !== null) {
        clearTimeout(undoTimerRef.current);
        undoTimerRef.current = null;
      }
    }
  }, [
    currentCardIndex,
    sessionCards.length,
    showSessionSummary,
    isShowingInsight,
    endSession,
    setReviewInProgress,
    toast,
  ]);

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

  if (showSessionSummary) {
    const sessionDuration =
      sessionStartedAt && sessionCompletedAt ? sessionCompletedAt - sessionStartedAt : 0;
    const remaining = sessionCards.length - currentCardIndex;
    const stats = sessionStatsQuery.data;
    const statsLoading = sessionStatsQuery.isLoading;
    const reviewedCount = stats?.cards_reviewed ?? cardsReviewed;

    return (
      <section className="mx-auto flex w-full max-w-[720px] flex-col gap-4 px-4 py-6 sm:px-6 lg:px-0">
        <SessionSummary
          cardsReviewed={reviewedCount}
          sessionDurationMs={sessionDuration}
          cardsRemaining={Math.max(0, remaining)}
          patternsDetected={insightsSeen}
          cardsGraduated={statsLoading ? undefined : stats?.cards_graduated}
          cardsLapsed={statsLoading ? undefined : stats?.cards_lapsed}
          tomorrowDueCount={statsLoading ? undefined : stats?.tomorrow_due_count}
          tomorrowEstimatedMinutes={statsLoading ? undefined : stats?.tomorrow_estimated_minutes}
          onDismiss={dismissSessionSummary}
          onReviewAgain={statsLoading ? undefined : handleReviewAgain}
          isLoadingStats={statsLoading && !sessionStatsQuery.isError}
        />
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

      {isShowingInsight && currentInsight ? (
        <InsightCard
          icon={currentInsight.icon}
          label={currentInsight.delivery_interval >= 10 ? "Quick insight" : "Pattern detected"}
          title={currentInsight.title}
          text={currentInsight.text}
          variant="inline"
          severity={currentInsight.severity}
          actionLabel={currentInsight.action_label ?? undefined}
          actionHref={currentInsight.action_href ?? undefined}
          onDismiss={handleDismissInsight}
        />
      ) : cardsLoading || !currentCard ? (
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
