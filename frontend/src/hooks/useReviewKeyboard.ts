"use client";

import { useEffect } from "react";
import { useReviewStore } from "@/stores/review-store";

export function useReviewKeyboard() {
  const isRevealed = useReviewStore((s) => s.isRevealed);
  const revealCard = useReviewStore((s) => s.revealCard);
  const toggleJpDefinition = useReviewStore((s) => s.toggleJpDefinition);
  const sessionCards = useReviewStore((s) => s.sessionCards);

  useEffect(() => {
    if (sessionCards.length === 0) return;

    function handleKeyDown(e: KeyboardEvent) {
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
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [sessionCards.length, isRevealed, revealCard, toggleJpDefinition]);
}
