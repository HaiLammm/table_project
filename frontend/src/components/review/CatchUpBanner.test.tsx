// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CatchUpBanner } from "./CatchUpBanner";

describe("CatchUpBanner", () => {
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

  it("does not render when overdue count is below the catch-up threshold", async () => {
    await act(async () => {
      root.render(
        <CatchUpBanner
          overdueCount={99}
          queueMode="full"
          onStartCatchUp={vi.fn()}
          onReviewAll={vi.fn()}
        />,
      );
    });

    expect(container.textContent).toBe("");
  });

  it("renders the catch-up suggestion when overdue count reaches 100", async () => {
    await act(async () => {
      root.render(
        <CatchUpBanner
          overdueCount={120}
          queueMode="full"
          onStartCatchUp={vi.fn()}
          onReviewAll={vi.fn()}
        />,
      );
    });

    expect(container.textContent).toContain(
      "You have 120 cards. We suggest starting with the 30 most overdue.",
    );
    expect(container.textContent).toContain("Start catch-up");
    expect(container.textContent).toContain("Review all");
  });
});
