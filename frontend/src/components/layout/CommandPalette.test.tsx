// @vitest-environment jsdom

import { act, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CommandPalette } from "./CommandPalette";

const pushMock = vi.fn();
const useVocabularySearchMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("@/hooks/useVocabularySearch", () => ({
  useVocabularySearch: (query: string) => useVocabularySearchMock(query),
}));

const mockWord = {
  id: 7,
  term: "protocol",
  language: "en",
  parent_id: null,
  cefr_level: "B2",
  jlpt_level: null,
  part_of_speech: "noun",
  definitions: [{ id: 1, language: "en", definition: "A set of rules", ipa: null, examples: [], source: "seed", validated_against_jmdict: false }],
  created_at: null,
};

function Harness() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <input aria-label="outside-input" />
      <button type="button" onClick={() => setOpen(true)}>
        Open palette
      </button>
      <CommandPalette open={open} onOpenChange={setOpen} />
    </>
  );
}

function buildSearchResult(query: string) {
  return {
    isLoading: false,
    isError: false,
    data:
      query.length >= 2
        ? {
            items: [mockWord],
            total: 1,
            page: 1,
            page_size: 20,
            has_next: false,
          }
        : {
            items: [],
            total: 0,
            page: 1,
            page_size: 20,
            has_next: false,
          },
  };
}

describe("CommandPalette", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    globalThis.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    HTMLElement.prototype.scrollIntoView = vi.fn();
    window.localStorage.clear();
    vi.clearAllMocks();
    useVocabularySearchMock.mockImplementation((query: string) => buildSearchResult(query));
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    document.body.innerHTML = "";
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  });

  const renderComponent = async () => {
    await act(async () => {
      root.render(<Harness />);
    });
  };

  const getPaletteInput = () => {
    return document.querySelector('input[placeholder="Search vocabulary, collections, or pages..."]') as HTMLInputElement | null;
  };

  const openWithShortcut = async () => {
    await act(async () => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }));
    });
  };

  const typeQuery = async (value: string) => {
    const input = getPaletteInput();
    if (input === null) {
      throw new Error("Palette input not found");
    }

    await act(async () => {
      const valueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
      valueSetter?.call(input, value);
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
    });
  };

  it("opens on Ctrl+K and closes on Escape", async () => {
    await renderComponent();
    expect(getPaletteInput()).toBeNull();

    await openWithShortcut();
    expect(getPaletteInput()).not.toBeNull();

    await act(async () => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    });

    expect(getPaletteInput()).toBeNull();
  });

  it("does not open when focus is inside another input", async () => {
    await renderComponent();

    const outsideInput = document.querySelector('input[aria-label="outside-input"]') as HTMLInputElement | null;
    outsideInput?.focus();

    await act(async () => {
      outsideInput?.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }));
    });

    expect(getPaletteInput()).toBeNull();
  });

  it("renders Pages, Collections, and Words groups for a query", async () => {
    await renderComponent();
    await openWithShortcut();
    await typeQuery("set");

    expect(document.body.textContent).toContain("Pages");
    expect(document.body.textContent).toContain("Collections");
    expect(document.body.textContent).toContain("Words");
    expect(document.body.textContent).toContain("Settings");
    expect(document.body.textContent).toContain("protocol");
  });

  it("stores selected results in recent searches and re-renders them on reopen", async () => {
    await renderComponent();
    await openWithShortcut();
    await typeQuery("pro");

    const result = Array.from(document.querySelectorAll("[cmdk-item]"))
      .find((item) => item.textContent?.includes("protocol"));

    await act(async () => {
      result?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(pushMock).toHaveBeenCalledWith("/vocabulary/7");

    const stored = window.localStorage.getItem("command-palette-recent");
    expect(stored).not.toBeNull();
    expect(stored).toContain("protocol");

    await act(async () => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true, bubbles: true }));
    });

    expect(document.body.textContent).toContain("Recent Searches");
    expect(document.body.textContent).toContain("protocol");
  });

  it("navigates with arrow keys and Enter", async () => {
    await renderComponent();
    await openWithShortcut();
    await typeQuery("set");

    const input = getPaletteInput();
    if (input === null) {
      throw new Error("Palette input not found");
    }

    await act(async () => {
      input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
      input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    });

    expect(pushMock).toHaveBeenCalledWith("/settings");
  });
});
