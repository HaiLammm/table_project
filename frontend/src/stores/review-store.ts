import { create } from "zustand";
import type { DiagnosticInsight } from "@/types/diagnostics";
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
  activeRating: number | null;

  previousCardIndex: number | null;
  sessionStartedAt: number | null;
  sessionCompletedAt: number | null;
  cardsReviewed: number;
  pendingInsights: DiagnosticInsight[];
  currentInsight: DiagnosticInsight | null;
  isShowingInsight: boolean;
  insightsSeen: number;
  undoAvailableUntil: number | null;
  lastRatedCardId: number | null;
  ratingLabelForUndo: string | null;
  showSessionSummary: boolean;

  setSessionCards: (cards: SessionCard[]) => void;
  setPendingInsights: (insights: DiagnosticInsight[]) => void;
  showNextInsight: () => void;
  dismissInsight: () => void;
  revealCard: () => void;
  nextCard: () => void;
  toggleJpDefinition: () => void;
  resetSession: () => void;
  setRatingInProgress: (inProgress: boolean) => void;
  setLastRating: (rating: number | null) => void;
  setActiveRating: (rating: number | null) => void;
  setRevealedAt: (timestamp: number | null) => void;

  rateCardAction: (rating: number, cardId: number, label: string) => void;
  undoLastRating: () => void;
  startSession: (cards: SessionCard[]) => void;
  incrementCardsReviewed: () => void;
  endSession: () => void;
  dismissSessionSummary: () => void;
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
  activeRating: null,

  previousCardIndex: null,
  sessionStartedAt: null,
  sessionCompletedAt: null,
  cardsReviewed: 0,
  pendingInsights: [],
  currentInsight: null,
  isShowingInsight: false,
  insightsSeen: 0,
  undoAvailableUntil: null,
  lastRatedCardId: null,
  ratingLabelForUndo: null,
  showSessionSummary: false,

  setSessionCards: (cards) =>
    set({
      sessionCards: cards,
      currentCardIndex: 0,
      isRevealed: false,
      showJpDefinition: false,
      isRatingInProgress: false,
      lastRating: null,
      revealedAt: null,
      activeRating: null,
      pendingInsights: [],
      currentInsight: null,
      isShowingInsight: false,
      insightsSeen: 0,
    }),

  setPendingInsights: (insights) =>
    set({
      pendingInsights: insights,
      currentInsight: null,
      isShowingInsight: false,
    }),

  showNextInsight: () =>
    set((state) => {
      if (state.isShowingInsight || state.pendingInsights.length === 0) return state;

      const nextInsight = state.pendingInsights[0];
      if (!nextInsight || state.currentCardIndex === 0) return state;
      if (state.currentCardIndex % nextInsight.delivery_interval !== 0) return state;

      return {
        currentInsight: nextInsight,
        pendingInsights: state.pendingInsights.slice(1),
        isShowingInsight: true,
        isRevealed: false,
        showJpDefinition: false,
        isRatingInProgress: false,
        activeRating: null,
      };
    }),

  dismissInsight: () =>
    set((state) => {
      if (!state.isShowingInsight) return state;
      return {
        currentInsight: null,
        isShowingInsight: false,
        insightsSeen: state.insightsSeen + 1,
      };
    }),

  revealCard: () => set({ isRevealed: true, revealedAt: Date.now() }),

  nextCard: () =>
    set((state) => ({
      currentCardIndex: state.currentCardIndex + 1,
      isRevealed: false,
      showJpDefinition: false,
      isRatingInProgress: false,
      lastRating: null,
      activeRating: null,
    })),

  toggleJpDefinition: () => set((state) => ({ showJpDefinition: !state.showJpDefinition })),

  resetSession: () =>
    set({
      currentCardIndex: 0,
      isRevealed: false,
      showJpDefinition: false,
      sessionCards: [],
      sessionStartedAt: null,
      sessionCompletedAt: null,
      cardsReviewed: 0,
      pendingInsights: [],
      currentInsight: null,
      isShowingInsight: false,
      insightsSeen: 0,
      isRatingInProgress: false,
      lastRating: null,
      revealedAt: null,
      activeRating: null,
    }),

  setRatingInProgress: (inProgress) => set({ isRatingInProgress: inProgress }),

  setLastRating: (rating) => set({ lastRating: rating }),

  setActiveRating: (rating) => set({ activeRating: rating }),

  setRevealedAt: (timestamp) => set({ revealedAt: timestamp }),

  rateCardAction: (_rating: number, cardId: number, label: string) =>
    set((state) => ({
      previousCardIndex: state.currentCardIndex,
      lastRatedCardId: cardId,
      ratingLabelForUndo: label,
      undoAvailableUntil: Date.now() + 3000,
    })),

  undoLastRating: () =>
    set((state) => {
      if (state.previousCardIndex === null) return state;
      return {
        currentCardIndex: state.previousCardIndex,
        isRevealed: true,
        undoAvailableUntil: null,
        lastRatedCardId: null,
        ratingLabelForUndo: null,
        previousCardIndex: null,
        isRatingInProgress: false,
        lastRating: null,
        activeRating: null,
      };
    }),

  startSession: (cards) =>
    set({
      sessionCards: cards,
      currentCardIndex: 0,
      sessionStartedAt: Date.now(),
      sessionCompletedAt: null,
      cardsReviewed: 0,
      pendingInsights: [],
      currentInsight: null,
      isShowingInsight: false,
      insightsSeen: 0,
      showSessionSummary: false,
      isRevealed: false,
      showJpDefinition: false,
      isRatingInProgress: false,
      lastRating: null,
      revealedAt: null,
      activeRating: null,
      undoAvailableUntil: null,
      lastRatedCardId: null,
      ratingLabelForUndo: null,
      previousCardIndex: null,
    }),

  incrementCardsReviewed: () =>
    set((state) => ({
      cardsReviewed: state.cardsReviewed + 1,
    })),

  endSession: () =>
    set({
      sessionCompletedAt: Date.now(),
      currentInsight: null,
      isShowingInsight: false,
      showSessionSummary: true,
      undoAvailableUntil: null,
      lastRatedCardId: null,
      ratingLabelForUndo: null,
      previousCardIndex: null,
    }),

  dismissSessionSummary: () =>
    set({
      showSessionSummary: false,
      currentCardIndex: 0,
      isRevealed: false,
      showJpDefinition: false,
      sessionCards: [],
      sessionStartedAt: null,
      sessionCompletedAt: null,
      cardsReviewed: 0,
      pendingInsights: [],
      currentInsight: null,
      isShowingInsight: false,
      insightsSeen: 0,
      isRatingInProgress: false,
      lastRating: null,
      revealedAt: null,
      activeRating: null,
    }),
}));
