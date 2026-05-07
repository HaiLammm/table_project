// @vitest-environment jsdom

import { describe, expect, it } from "vitest";
import { useReviewStore } from "./review-store";
import type { DiagnosticInsight } from "@/types/diagnostics";
import type { SessionCard } from "@/types/srs";

function makeCard(id: number): SessionCard {
  return {
    id,
    term_id: null,
    language: null,
    due_at: new Date().toISOString(),
    fsrs_state: {},
    stability: 0,
    difficulty: 0,
    reps: 0,
    lapses: 0,
    term: null,
  };
}

function makeInsight(id: number, deliveryInterval = 5): DiagnosticInsight {
  return {
    id,
    type: "time_of_day_pattern",
    severity: "info",
    icon: "clock",
    title: `Insight ${id}`,
    text: `Insight body ${id}`,
    action_label: null,
    action_href: null,
    delivery_interval: deliveryInterval,
  };
}

describe("useReviewStore", () => {
  it("initializes with default values", () => {
    const state = useReviewStore.getState();
    expect(state.currentCardIndex).toBe(0);
    expect(state.isRevealed).toBe(false);
    expect(state.sessionCards).toEqual([]);
    expect(state.previousCardIndex).toBeNull();
    expect(state.sessionStartedAt).toBeNull();
    expect(state.sessionCompletedAt).toBeNull();
    expect(state.cardsReviewed).toBe(0);
    expect(state.pendingInsights).toEqual([]);
    expect(state.currentInsight).toBeNull();
    expect(state.isShowingInsight).toBe(false);
    expect(state.insightsSeen).toBe(0);
    expect(state.undoAvailableUntil).toBeNull();
    expect(state.lastRatedCardId).toBeNull();
    expect(state.ratingLabelForUndo).toBeNull();
    expect(state.showSessionSummary).toBe(false);
  });

  it("rateCardAction sets undo state", () => {
    const store = useReviewStore;
    store.setState({ currentCardIndex: 3, sessionCards: [makeCard(1), makeCard(2), makeCard(3), makeCard(4)] });

    useReviewStore.getState().rateCardAction(3, 42, "Good");

    const state = useReviewStore.getState();
    expect(state.previousCardIndex).toBe(3);
    expect(state.lastRatedCardId).toBe(42);
    expect(state.ratingLabelForUndo).toBe("Good");
    expect(state.undoAvailableUntil).toBeGreaterThan(Date.now());
  });

  it("undoLastRating restores previous card index", () => {
    const store = useReviewStore;
    const cards = [makeCard(1), makeCard(2)];
    store.setState({
      sessionCards: cards,
      currentCardIndex: 1,
      previousCardIndex: 0,
      isRevealed: false,
    });

    useReviewStore.getState().undoLastRating();

    const state = useReviewStore.getState();
    expect(state.currentCardIndex).toBe(0);
    expect(state.isRevealed).toBe(true);
    expect(state.undoAvailableUntil).toBeNull();
    expect(state.lastRatedCardId).toBeNull();
    expect(state.ratingLabelForUndo).toBeNull();
    expect(state.previousCardIndex).toBeNull();
    expect(state.isRatingInProgress).toBe(false);
  });

  it("undoLastRating does nothing when previousCardIndex is null", () => {
    const store = useReviewStore;
    store.setState({
      currentCardIndex: 2,
      previousCardIndex: null,
      isRevealed: false,
    });

    useReviewStore.getState().undoLastRating();

    const state = useReviewStore.getState();
    expect(state.currentCardIndex).toBe(2);
    expect(state.isRevealed).toBe(false);
  });

  it("startSession initializes session state", () => {
    const cards = [makeCard(1), makeCard(2), makeCard(3)];

    useReviewStore.getState().startSession(cards);

    const state = useReviewStore.getState();
    expect(state.sessionCards).toEqual(cards);
    expect(state.currentCardIndex).toBe(0);
    expect(state.sessionStartedAt).toBeGreaterThan(0);
    expect(state.cardsReviewed).toBe(0);
    expect(state.showSessionSummary).toBe(false);
    expect(state.isRevealed).toBe(false);
    expect(state.undoAvailableUntil).toBeNull();
  });

  it("incrementCardsReviewed increases count", () => {
    useReviewStore.setState({ cardsReviewed: 5 });

    useReviewStore.getState().incrementCardsReviewed();

    expect(useReviewStore.getState().cardsReviewed).toBe(6);
  });

  it("endSession shows summary while preserving session metrics", () => {
    useReviewStore.setState({
      sessionStartedAt: Date.now(),
      cardsReviewed: 10,
      undoAvailableUntil: Date.now() + 5000,
      lastRatedCardId: 99,
      ratingLabelForUndo: "Hard",
      previousCardIndex: 3,
    });

    useReviewStore.getState().endSession();

    const state = useReviewStore.getState();
    expect(state.showSessionSummary).toBe(true);
    expect(state.sessionStartedAt).not.toBeNull();
    expect(state.sessionCompletedAt).not.toBeNull();
    expect(state.cardsReviewed).toBe(10);
    expect(state.undoAvailableUntil).toBeNull();
    expect(state.lastRatedCardId).toBeNull();
    expect(state.ratingLabelForUndo).toBeNull();
    expect(state.previousCardIndex).toBeNull();
  });

  it("dismissSessionSummary resets all session-related state", () => {
    useReviewStore.setState({
      showSessionSummary: true,
      sessionCards: [makeCard(1)],
      currentCardIndex: 1,
      isRevealed: true,
      isRatingInProgress: true,
      lastRating: 1,
      activeRating: 1,
    });

    useReviewStore.getState().dismissSessionSummary();

    const state = useReviewStore.getState();
    expect(state.showSessionSummary).toBe(false);
    expect(state.sessionCards).toEqual([]);
    expect(state.sessionStartedAt).toBeNull();
    expect(state.sessionCompletedAt).toBeNull();
    expect(state.cardsReviewed).toBe(0);
    expect(state.currentCardIndex).toBe(0);
    expect(state.isRevealed).toBe(false);
    expect(state.isRatingInProgress).toBe(false);
    expect(state.lastRating).toBeNull();
    expect(state.activeRating).toBeNull();
  });

  it("shows and dismisses insights without advancing the card counter", () => {
    useReviewStore.setState({
      sessionCards: [makeCard(1), makeCard(2), makeCard(3), makeCard(4), makeCard(5), makeCard(6)],
      currentCardIndex: 5,
      pendingInsights: [makeInsight(101, 5)],
      isShowingInsight: false,
      currentInsight: null,
      insightsSeen: 0,
    });

    useReviewStore.getState().showNextInsight();

    let state = useReviewStore.getState();
    expect(state.isShowingInsight).toBe(true);
    expect(state.currentInsight?.id).toBe(101);
    expect(state.pendingInsights).toEqual([]);
    expect(state.currentCardIndex).toBe(5);

    useReviewStore.getState().dismissInsight();

    state = useReviewStore.getState();
    expect(state.isShowingInsight).toBe(false);
    expect(state.currentInsight).toBeNull();
    expect(state.insightsSeen).toBe(1);
    expect(state.currentCardIndex).toBe(5);
  });

  it("respects delivery interval before showing the next insight", () => {
    useReviewStore.setState({
      currentCardIndex: 5,
      pendingInsights: [makeInsight(201, 10)],
      isShowingInsight: false,
      currentInsight: null,
    });

    useReviewStore.getState().showNextInsight();

    let state = useReviewStore.getState();
    expect(state.isShowingInsight).toBe(false);
    expect(state.currentInsight).toBeNull();
    expect(state.pendingInsights).toHaveLength(1);

    useReviewStore.setState({ currentCardIndex: 10 });
    useReviewStore.getState().showNextInsight();

    state = useReviewStore.getState();
    expect(state.isShowingInsight).toBe(true);
    expect(state.currentInsight?.id).toBe(201);
  });

  it("resets session correctly", () => {
    useReviewStore.setState({
      sessionCards: [makeCard(1)],
      currentCardIndex: 1,
      isRevealed: true,
      isRatingInProgress: true,
      lastRating: 3,
      activeRating: 3,
    });

    useReviewStore.getState().resetSession();

    const state = useReviewStore.getState();
    expect(state.sessionCards).toEqual([]);
    expect(state.currentCardIndex).toBe(0);
    expect(state.isRevealed).toBe(false);
    expect(state.isRatingInProgress).toBe(false);
  });

  it("does not show insight at index 0", () => {
    useReviewStore.setState({
      sessionCards: [makeCard(1), makeCard(2), makeCard(3)],
      currentCardIndex: 0,
      pendingInsights: [makeInsight(301, 5)],
      isShowingInsight: false,
      currentInsight: null,
    });

    useReviewStore.getState().showNextInsight();

    const state = useReviewStore.getState();
    expect(state.isShowingInsight).toBe(false);
    expect(state.currentInsight).toBeNull();
  });

  it("does not show insight when already showing one", () => {
    useReviewStore.setState({
      sessionCards: [makeCard(1), makeCard(2), makeCard(3), makeCard(4), makeCard(5), makeCard(6)],
      currentCardIndex: 5,
      pendingInsights: [makeInsight(401, 5)],
      isShowingInsight: true,
      currentInsight: makeInsight(999, 5),
    });

    useReviewStore.getState().showNextInsight();

    const state = useReviewStore.getState();
    expect(state.isShowingInsight).toBe(true);
    expect(state.currentInsight?.id).toBe(999);
    expect(state.pendingInsights).toHaveLength(1);
  });

  it("dismissInsight is no-op when not showing insight", () => {
    useReviewStore.setState({
      isShowingInsight: false,
      currentInsight: null,
      insightsSeen: 0,
    });

    useReviewStore.getState().dismissInsight();

    const state = useReviewStore.getState();
    expect(state.insightsSeen).toBe(0);
  });
});
