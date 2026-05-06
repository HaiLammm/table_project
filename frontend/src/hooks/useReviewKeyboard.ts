"use client";

import { useEffect, useRef } from "react";
import { useReviewStore } from "@/stores/review-store";
import type { RatingValue } from "@/types/srs";

export function useReviewKeyboard(onRate?: (rating: RatingValue) => void) {
  const isRevealed = useReviewStore((s) => s.isRevealed);
  const isRatingInProgress = useReviewStore((s) => s.isRatingInProgress);
  const revealCard = useReviewStore((s) => s.revealCard);
  const toggleJpDefinition = useReviewStore((s) => s.toggleJpDefinition);
  const sessionCards = useReviewStore((s) => s.sessionCards);

  const onRateRef = useRef(onRate);
  onRateRef.current = onRate;

  useEffect(() => {
    if (sessionCards.length === 0) return;

    let mounted = true;

    function handleKeyDown(e: KeyboardEvent) {
      if (!mounted) return;

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

      if (isRevealed && !isRatingInProgress && onRateRef.current) {
        if (e.code === "Digit1") {
          e.preventDefault();
          onRateRef.current(1);
          return;
        }
        if (e.code === "Digit2") {
          e.preventDefault();
          onRateRef.current(2);
          return;
        }
        if (e.code === "Digit3") {
          e.preventDefault();
          onRateRef.current(3);
          return;
        }
        if (e.code === "Digit4") {
          e.preventDefault();
          onRateRef.current(4);
          return;
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      mounted = false;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [sessionCards.length, isRevealed, isRatingInProgress, revealCard, toggleJpDefinition]);
}
