import { create } from "zustand";
import type { SessionCard } from "@/types/srs";

type QueueMode = "full" | "catchup";

type ReviewStore = {
  queueMode: QueueMode;
  setQueueMode: (mode: QueueMode) => void;

  currentCardIndex: number;
  isRevealed: boolean;
  showJpDefinition: boolean;
  sessionCards: SessionCard[];

  isRatingInProgress: boolean;
  lastRating: number | null;
  revealedAt: number | null;

  setSessionCards: (cards: SessionCard[]) => void;
  revealCard: () => void;
  nextCard: () => void;
  toggleJpDefinition: () => void;
  resetSession: () => void;
  setRatingInProgress: (inProgress: boolean) => void;
  setLastRating: (rating: number | null) => void;
};

export const useReviewStore = create<ReviewStore>((set) => ({
  queueMode: "full",
  setQueueMode: (mode) => set({ queueMode: mode }),

  currentCardIndex: 0,
  isRevealed: false,
  showJpDefinition: false,
  sessionCards: [],

  isRatingInProgress: false,
  lastRating: null,
  revealedAt: null,

  setSessionCards: (cards) =>
    set({
      sessionCards: cards,
      currentCardIndex: 0,
      isRevealed: false,
      showJpDefinition: false,
      isRatingInProgress: false,
      lastRating: null,
      revealedAt: null,
    }),

  revealCard: () => set({ isRevealed: true, revealedAt: Date.now() }),

  nextCard: () =>
    set((state) => ({
      currentCardIndex: state.currentCardIndex + 1,
      isRevealed: false,
      showJpDefinition: false,
      isRatingInProgress: false,
      lastRating: null,
    })),

  toggleJpDefinition: () => set((state) => ({ showJpDefinition: !state.showJpDefinition })),

  resetSession: () =>
    set({
      currentCardIndex: 0,
      isRevealed: false,
      showJpDefinition: false,
      sessionCards: [],
      isRatingInProgress: false,
      lastRating: null,
      revealedAt: null,
    }),

  setRatingInProgress: (inProgress) => set({ isRatingInProgress: inProgress }),

  setLastRating: (rating) => set({ lastRating: rating }),
}));
