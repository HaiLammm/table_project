// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { QueueHeader } from "./QueueHeader";

describe("QueueHeader", () => {
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

  it("renders the neutral queue context line and stat chips", async () => {
    await act(async () => {
      root.render(<QueueHeader dueCount={12} estimatedMinutes={2} />);
    });

    expect(container.textContent).toContain("Today's Queue");
    expect(container.textContent).toContain("12 cards ready. ~2 min estimated.");
    expect(container.textContent).toContain("Ready12 cards");
    expect(container.textContent).toContain("Estimate~2 min");
  });
});
