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

  setSessionCards: (cards: SessionCard[]) => void;
  revealCard: () => void;
  nextCard: () => void;
  toggleJpDefinition: () => void;
  resetSession: () => void;
};

export const useReviewStore = create<ReviewStore>((set) => ({
  queueMode: "full",
  setQueueMode: (mode) => set({ queueMode: mode }),

  currentCardIndex: 0,
  isRevealed: false,
  showJpDefinition: false,
  sessionCards: [],

  setSessionCards: (cards) =>
    set({ sessionCards: cards, currentCardIndex: 0, isRevealed: false, showJpDefinition: false }),

  revealCard: () => set({ isRevealed: true }),

  nextCard: () =>
    set((state) => ({
      currentCardIndex: state.currentCardIndex + 1,
      isRevealed: false,
      showJpDefinition: false,
    })),

  toggleJpDefinition: () => set((state) => ({ showJpDefinition: !state.showJpDefinition })),

  resetSession: () =>
    set({
      currentCardIndex: 0,
      isRevealed: false,
      showJpDefinition: false,
      sessionCards: [],
    }),
}));
