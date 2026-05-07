"use client";

import { useEffect, useEffectEvent } from "react";
import { useReviewStore } from "@/stores/review-store";
import type { RatingValue } from "@/types/srs";

export function useReviewKeyboard(
  onRate?: (rating: RatingValue) => void,
  onEndSession?: () => void,
  onUndo?: () => void,
  onDismissInsight?: () => void,
) {
  const isRevealed = useReviewStore((s) => s.isRevealed);
  const isShowingInsight = useReviewStore((s) => s.isShowingInsight);
  const isRatingInProgress = useReviewStore((s) => s.isRatingInProgress);
  const revealCard = useReviewStore((s) => s.revealCard);
  const toggleJpDefinition = useReviewStore((s) => s.toggleJpDefinition);
  const sessionCards = useReviewStore((s) => s.sessionCards);
  const undoAvailableUntil = useReviewStore((s) => s.undoAvailableUntil);

  const handleRate = useEffectEvent((rating: RatingValue) => {
    onRate?.(rating);
  });
  const handleEndSession = useEffectEvent(() => {
    onEndSession?.();
  });
  const handleUndo = useEffectEvent(() => {
    onUndo?.();
  });
  const handleDismissInsight = useEffectEvent(() => {
    onDismissInsight?.();
  });

  useEffect(() => {
    if (sessionCards.length === 0) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.code === "Escape") {
        e.preventDefault();
        handleEndSession();
        return;
      }

      if ((e.ctrlKey || e.metaKey) && e.code === "KeyZ") {
        if (isShowingInsight) return;
        if (undoAvailableUntil !== null && Date.now() < undoAvailableUntil && onUndo) {
          e.preventDefault();
          handleUndo();
        }
        return;
      }

      if (isShowingInsight) {
        if (e.code === "Tab") {
          e.preventDefault();
        }
        if (e.code === "Space") {
          e.preventDefault();
          handleDismissInsight();
        }
        return;
      }

      if (e.code === "Space" && !isRevealed) {
        e.preventDefault();
        revealCard();
        return;
      }

      if (e.code === "Tab" && isRevealed) {
        e.preventDefault();
        toggleJpDefinition();
        return;
      }

      if (isRevealed && !isRatingInProgress && onRate) {
        if (e.code === "Digit1") {
          e.preventDefault();
          handleRate(1);
          return;
        }
        if (e.code === "Digit2") {
          e.preventDefault();
          handleRate(2);
          return;
        }
        if (e.code === "Digit3") {
          e.preventDefault();
          handleRate(3);
          return;
        }
        if (e.code === "Digit4") {
          e.preventDefault();
          handleRate(4);
          return;
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    sessionCards.length,
    isRevealed,
    isShowingInsight,
    isRatingInProgress,
    onRate,
    onUndo,
    undoAvailableUntil,
    revealCard,
    toggleJpDefinition,
  ]);
}
