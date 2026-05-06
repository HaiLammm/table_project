// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Topbar } from "./Topbar";

const onSearchOpen = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

describe("Topbar", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    vi.clearAllMocks();
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  });

  it("opens the command palette from the search button", async () => {
    await act(async () => {
      root.render(<Topbar mobileOpen={false} onMenuToggle={vi.fn()} onSearchOpen={onSearchOpen} />);
    });

    const button = Array.from(container.querySelectorAll("button")).find((item) => item.textContent?.includes("Search"));

    await act(async () => {
      button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(onSearchOpen).toHaveBeenCalledOnce();
  });
});
