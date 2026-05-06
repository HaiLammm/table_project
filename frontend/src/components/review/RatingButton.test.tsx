// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RatingButton } from "./RatingButton";

describe("RatingButton", () => {
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

  it("renders Again variant with label, interval, and key number", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="again" interval="<1m" onRate={onRate} />,
      );
    });

    expect(container.textContent).toContain("1");
    expect(container.textContent).toContain("Again");
    expect(container.textContent).toContain("<1m");
  });

  it("renders Hard variant with label, interval, and key number", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="hard" interval="6m" onRate={onRate} />,
      );
    });

    expect(container.textContent).toContain("2");
    expect(container.textContent).toContain("Hard");
    expect(container.textContent).toContain("6m");
  });

  it("renders Good variant with label, interval, and key number", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="good" interval="1d" onRate={onRate} />,
      );
    });

    expect(container.textContent).toContain("3");
    expect(container.textContent).toContain("Good");
    expect(container.textContent).toContain("1d");
  });

  it("renders Easy variant with label, interval, and key number", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="easy" interval="4d" onRate={onRate} />,
      );
    });

    expect(container.textContent).toContain("4");
    expect(container.textContent).toContain("Easy");
    expect(container.textContent).toContain("4d");
  });

  it("fires onRate callback on click", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="good" interval="1d" onRate={onRate} />,
      );
    });

    const button = container.querySelector("button");
    expect(button).not.toBeNull();

    await act(async () => {
      button!.click();
    });

    expect(onRate).toHaveBeenCalledTimes(1);
  });

  it("does not fire onRate when disabled", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="good" interval="1d" onRate={onRate} disabled />,
      );
    });

    const button = container.querySelector("button");
    expect(button).not.toBeNull();
    expect(button!.disabled).toBe(true);

    await act(async () => {
      button!.click();
    });

    expect(onRate).not.toHaveBeenCalled();
  });

  it("has correct ARIA label containing label and interval", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="hard" interval="6m" onRate={onRate} />,
      );
    });

    const button = container.querySelector("button");
    expect(button).not.toBeNull();
    expect(button!.getAttribute("aria-label")).toBe(
      "Rate as Hard, next review in 6m",
    );
  });

  it("has correct ARIA label for Again variant", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="again" interval="<1m" onRate={onRate} />,
      );
    });

    const button = container.querySelector("button");
    expect(button).not.toBeNull();
    expect(button!.getAttribute("aria-label")).toBe(
      "Rate as Again, next review in <1m",
    );
  });

  it("button is enabled by default", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="good" interval="1d" onRate={onRate} />,
      );
    });

    const button = container.querySelector("button");
    expect(button).not.toBeNull();
    expect(button!.disabled).toBe(false);
  });

  it("renders key number badge in top-right corner", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="again" interval="<1m" onRate={onRate} />,
      );
    });

    const badge = container.querySelector(
      "span.absolute.top-1.right-1\\.5",
    );
    expect(badge).not.toBeNull();
    expect(badge!.textContent).toContain("1");
  });

  it("renders interval text below label", async () => {
    const onRate = vi.fn();
    await act(async () => {
      root.render(
        <RatingButton variant="easy" interval="4d" onRate={onRate} />,
      );
    });

    const intervalSpan = container.querySelector(
      '[class*="text-\\[11px\\]"]',
    );
    expect(intervalSpan).not.toBeNull();
    expect(intervalSpan!.textContent).toBe("4d");
  });
});
