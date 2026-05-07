// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { InsightCard } from "./InsightCard";

vi.mock("next/link", () => ({
  default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
}));

describe("InsightCard", () => {
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

  it("renders content, hint, and aria attributes", async () => {
    await act(async () => {
      root.render(
        <InsightCard
          icon="clock"
          label="Quick insight"
          title="Morning sessions are a strength"
          text="Your accuracy looks strongest in the morning."
          variant="inline"
          severity="info"
        />,
      );
    });

    const insight = container.querySelector('[role="complementary"]');
    expect(insight).not.toBeNull();
    expect(insight?.getAttribute("aria-label")).toBe("Learning insight");
    expect(insight?.className).toContain("bg-zinc-900");
    expect(insight?.className).toContain("border-zinc-800");
    expect(container.textContent).toContain("Quick insight");
    expect(container.textContent).toContain("Morning sessions are a strength");
    expect(container.textContent).toContain("Press Space to continue");
  });

  it("applies severity styling and renders action link", async () => {
    await act(async () => {
      root.render(
        <InsightCard
          icon="alert-triangle"
          label="Pattern detected"
          title="One category needs reinforcement"
          text="Your noun cards are recalled less often than average."
          variant="inline"
          severity="warning"
          actionLabel="View analytics"
          actionHref="/dashboard"
        />,
      );
    });

    const warningIcon = container.querySelector(".text-amber-400");
    const actionLink = container.querySelector('a[href="/dashboard"]');

    expect(warningIcon).not.toBeNull();
    expect(actionLink?.textContent).toBe("View analytics");
  });

  it("fires dismiss callback when dismiss button is clicked", async () => {
    const onDismiss = vi.fn();

    await act(async () => {
      root.render(
        <InsightCard
          icon="trending-up"
          label="Pattern detected"
          title="Slow cards tend to slip"
          text="Cards taking over 10s are forgotten more often."
          variant="inline"
          severity="success"
          onDismiss={onDismiss}
        />,
      );
    });

    const dismissButton = container.querySelector("button");
    dismissButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});
