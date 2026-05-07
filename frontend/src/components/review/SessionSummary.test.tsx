// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SessionSummary } from "./SessionSummary";

describe("SessionSummary", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      false;
  });

  it("renders session stats", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={12}
          sessionDurationMs={135000}
          cardsRemaining={8}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).toContain("Session Complete");
    expect(container.textContent).toContain("12 cards reviewed in 2m 15s");
  });

  it("renders action buttons", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={0}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).toContain("View Dashboard");
    expect(container.textContent).toContain("Add Words");
  });

  it("formats duration with seconds only when under 1 minute", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={1}
          sessionDurationMs={45000}
          cardsRemaining={10}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).toContain("1 cards reviewed in 45s");
  });

  it("hides zero remaining cards line", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={3}
          sessionDurationMs={30000}
          cardsRemaining={0}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).not.toContain("0 cards remaining in queue");
  });

  it("renders pattern detection summary when insights were shown", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={7}
          sessionDurationMs={90000}
          cardsRemaining={3}
          patternsDetected={2}
          onDismiss={onDismiss}
        />,
      );
    });

    const dashboardLink = container.querySelector('a[href="/dashboard"]');
    expect(container.textContent).toContain("2 new patterns detected");
    expect(dashboardLink).not.toBeNull();
  });

  it("shows graduated line when cardsGraduated > 0", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={10}
          sessionDurationMs={300000}
          cardsRemaining={0}
          cardsGraduated={3}
          tomorrowDueCount={18}
          tomorrowEstimatedMinutes={3}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).toContain("3 cards graduated to mastered");
  });

  it("hides graduated line when cardsGraduated is 0 or undefined", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={2}
          tomorrowDueCount={10}
          tomorrowEstimatedMinutes={2}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).not.toContain("graduated to mastered");
  });

  it("always shows tomorrow estimate", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={0}
          tomorrowDueCount={18}
          tomorrowEstimatedMinutes={3}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).toContain("Tomorrow: ~18 cards, ~3 min");
  });

  it("shows Review Again button when cardsLapsed > 0 and onReviewAgain provided", async () => {
    const onDismiss = vi.fn();
    const onReviewAgain = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={0}
          cardsLapsed={2}
          onDismiss={onDismiss}
          onReviewAgain={onReviewAgain}
        />,
      );
    });

    expect(container.textContent).toContain("Review Again");
  });

  it("hides Review Again button when cardsLapsed is 0", async () => {
    const onDismiss = vi.fn();
    const onReviewAgain = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={0}
          cardsLapsed={0}
          onDismiss={onDismiss}
          onReviewAgain={onReviewAgain}
        />,
      );
    });

    expect(container.textContent).not.toContain("Review Again");
  });

  it("hides Review Again button when onReviewAgain is not provided even if cardsLapsed > 0", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={0}
          cardsLapsed={3}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).not.toContain("Review Again");
  });

  it("fires onReviewAgain callback when Review Again is clicked", async () => {
    const onDismiss = vi.fn();
    const onReviewAgain = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={0}
          cardsLapsed={2}
          onDismiss={onDismiss}
          onReviewAgain={onReviewAgain}
        />,
      );
    });

    const reviewAgainButton = Array.from(container.querySelectorAll("button")).find(
      (btn) => btn.textContent?.includes("Review Again"),
    );
    expect(reviewAgainButton).not.toBeNull();

    await act(async () => {
      reviewAgainButton!.click();
    });

    expect(onReviewAgain).toHaveBeenCalledOnce();
  });

  it("backward compat: works without new props (no crash, no delta lines)", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={2}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).toContain("Session Complete");
    expect(container.textContent).toContain("5 cards reviewed in 1m");
    expect(container.textContent).toContain("View Dashboard");
    expect(container.textContent).toContain("Add Words");
    expect(container.textContent).not.toContain("graduated to mastered");
    expect(container.textContent).not.toContain("Review Again");
  });

  it("shows skeleton when isLoadingStats is true", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={0}
          isLoadingStats={true}
          onDismiss={onDismiss}
        />,
      );
    });

    const skeletonBars = container.querySelectorAll(".animate-pulse");
    expect(skeletonBars.length).toBeGreaterThanOrEqual(2);
    expect(container.textContent).toContain("5 cards reviewed in 1m");
  });

  it("shows remaining cards when cardsRemaining > 0", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={5}
          sessionDurationMs={60000}
          cardsRemaining={3}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).toContain("3 cards remaining in queue");
  });

  it("formats duration with hours when over 60 minutes", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={50}
          sessionDurationMs={4320000}
          cardsRemaining={0}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).toContain("1h 12m");
  });

  it("formats duration between 10m and 60m", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <SessionSummary
          cardsReviewed={30}
          sessionDurationMs={720000}
          cardsRemaining={0}
          onDismiss={onDismiss}
        />,
      );
    });

    expect(container.textContent).toContain("12m");
  });
});