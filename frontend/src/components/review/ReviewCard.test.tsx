// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReviewCard } from "./ReviewCard";
import type { SessionCard } from "@/types/srs";

const mockCard: SessionCard = {
  id: 1,
  term_id: 42,
  language: "en",
  due_at: "2026-05-06T10:00:00Z",
  fsrs_state: {},
  stability: 1.0,
  difficulty: 0.3,
  reps: 2,
  lapses: 0,
  term: {
    id: 42,
    term: "protocol",
    language: "en",
    parent_id: null,
    cefr_level: "B2",
    jlpt_level: null,
    part_of_speech: "noun",
    definitions: [
      {
        id: 1,
        language: "en",
        definition: "A set of rules governing the exchange or transmission of data.",
        ipa: "ˈproʊtəkɔl",
        examples: [
          "The protocol was updated to improve security.",
          "HTTP is a widely used internet protocol.",
        ],
        source: "corpus",
        validated_against_jmdict: false,
      },
      {
        id: 2,
        language: "ja",
        definition: "プロトコル",
        ipa: null,
        examples: [],
        source: "corpus",
        validated_against_jmdict: false,
      },
    ],
    created_at: "2026-04-01T00:00:00Z",
  },
};

describe("ReviewCard", () => {
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

  it("renders front state with term, reading, metadata, session counter, and space hint", async () => {
    await act(async () => {
      root.render(
        <ReviewCard
          card={mockCard}
          currentIndex={0}
          totalCards={24}
          isRevealed={false}
          showJpDefinition={false}
          onRate={vi.fn()}
          isRatingInProgress={false}
          lastRating={null}
          activeRating={null}
          intervals={{ again: "<1m", hard: "6m", good: "1d", easy: "4d" }}
        />,
      );
    });

    expect(container.textContent).toContain("protocol");
    expect(container.textContent).toContain("プロトコル");
    expect(container.textContent).toContain("noun");
    expect(container.textContent).toContain("B2");
    expect(container.textContent).toContain("1/24");
    expect(container.textContent).toContain("Space");
    expect(container.textContent).toContain("reveal answer");
  });

  it("has correct accessibility attributes in front state", async () => {
    await act(async () => {
      root.render(
        <ReviewCard
          card={mockCard}
          currentIndex={0}
          totalCards={24}
          isRevealed={false}
          showJpDefinition={false}
          onRate={vi.fn()}
          isRatingInProgress={false}
          lastRating={null}
          activeRating={null}
          intervals={{ again: "<1m", hard: "6m", good: "1d", easy: "4d" }}
        />,
      );
    });

    const article = container.querySelector('[role="article"]');
    expect(article).not.toBeNull();
    expect(article?.getAttribute("aria-label")).toBe("Vocabulary card: protocol");
    expect(article?.getAttribute("tabindex")).toBe("0");
  });

  it("renders revealed state with definition, IPA, examples, CEFR badge, and rating buttons", async () => {
    await act(async () => {
      root.render(
        <ReviewCard
          card={mockCard}
          currentIndex={0}
          totalCards={24}
          isRevealed={true}
          showJpDefinition={false}
          onRate={vi.fn()}
          isRatingInProgress={false}
          lastRating={null}
          activeRating={null}
          intervals={{ again: "<1m", hard: "6m", good: "1d", easy: "4d" }}
        />,
      );
    });

    expect(container.textContent).toContain(
      "A set of rules governing the exchange or transmission of data.",
    );
    expect(container.textContent).toContain("ˈproʊtəkɔl");
    expect(container.textContent).toContain(
      "The protocol was updated to improve security.",
    );
    expect(container.textContent).toContain("B2");
    expect(container.textContent).toContain("Again");
    expect(container.textContent).toContain("Hard");
    expect(container.textContent).toContain("Good");
    expect(container.textContent).toContain("Easy");
  });

  it("does not show Space hint when revealed", async () => {
    await act(async () => {
      root.render(
        <ReviewCard
          card={mockCard}
          currentIndex={0}
          totalCards={24}
          isRevealed={true}
          showJpDefinition={false}
          onRate={vi.fn()}
          isRatingInProgress={false}
          lastRating={null}
          activeRating={null}
          intervals={{ again: "<1m", hard: "6m", good: "1d", easy: "4d" }}
        />,
      );
    });

    expect(container.textContent).not.toContain("reveal answer");
  });

  it("shows Japanese definition when showJpDefinition is true and card is revealed", async () => {
    await act(async () => {
      root.render(
        <ReviewCard
          card={mockCard}
          currentIndex={0}
          totalCards={24}
          isRevealed={true}
          showJpDefinition={true}
          onRate={vi.fn()}
          isRatingInProgress={false}
          lastRating={null}
          activeRating={null}
          intervals={{ again: "<1m", hard: "6m", good: "1d", easy: "4d" }}
        />,
      );
    });

    expect(container.textContent).toContain("Japanese definition");
  });

  it("does not show Japanese definition when card is not revealed", async () => {
    await act(async () => {
      root.render(
        <ReviewCard
          card={mockCard}
          currentIndex={0}
          totalCards={24}
          isRevealed={false}
          showJpDefinition={true}
          onRate={vi.fn()}
          isRatingInProgress={false}
          lastRating={null}
          activeRating={null}
          intervals={{ again: "<1m", hard: "6m", good: "1d", easy: "4d" }}
        />,
      );
    });

    expect(container.textContent).not.toContain("Japanese definition");
  });

  it("renders rating buttons group with correct aria attributes", async () => {
    await act(async () => {
      root.render(
        <ReviewCard
          card={mockCard}
          currentIndex={0}
          totalCards={24}
          isRevealed={true}
          showJpDefinition={false}
          onRate={vi.fn()}
          isRatingInProgress={false}
          lastRating={null}
          activeRating={null}
          intervals={{ again: "<1m", hard: "6m", good: "1d", easy: "4d" }}
        />,
      );
    });

    const ratingGroup = container.querySelector('[aria-label="Rate your recall"]');
    expect(ratingGroup).not.toBeNull();
    expect(ratingGroup?.getAttribute("role")).toBe("group");
  });

  it("shows fallback message when card has no English definition", async () => {
    const cardWithoutEn: SessionCard = {
      ...mockCard,
      term: {
        ...mockCard.term!,
        definitions: [
          {
            id: 1,
            language: "ja",
            definition: "プロトコル",
            ipa: null,
            examples: [],
            source: "corpus",
            validated_against_jmdict: false,
          },
        ],
      },
    };

    await act(async () => {
      root.render(
        <ReviewCard
          card={cardWithoutEn}
          currentIndex={0}
          totalCards={1}
          isRevealed={true}
          showJpDefinition={false}
          onRate={vi.fn()}
          isRatingInProgress={false}
          lastRating={null}
          activeRating={null}
          intervals={{ again: "<1m", hard: "6m", good: "1d", easy: "4d" }}
        />,
      );
    });

    expect(container.textContent).toContain("No definition available");
  });

  it("shows loading text when term is null", async () => {
    const cardWithoutTerm: SessionCard = {
      ...mockCard,
      term: null,
    };

    await act(async () => {
      root.render(
        <ReviewCard
          card={cardWithoutTerm}
          currentIndex={0}
          totalCards={1}
          isRevealed={false}
          showJpDefinition={false}
          onRate={vi.fn()}
          isRatingInProgress={false}
          lastRating={null}
          activeRating={null}
          intervals={{ again: "<1m", hard: "6m", good: "1d", easy: "4d" }}
        />,
      );
    });

    expect(container.textContent).toContain("Loading...");
  });
});
