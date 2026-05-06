// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TermAutoSuggest } from "./TermAutoSuggest";

const mockSearchResults = {
  isLoading: false,
  isError: false,
  data: {
    items: [] as any[],
    total: 0,
    page: 1,
    page_size: 20,
    has_next: false,
  },
};

const useVocabularySearchMock = vi.fn().mockImplementation(() => mockSearchResults);

vi.mock("@/hooks/useVocabularySearch", () => ({
  useVocabularySearch: () => useVocabularySearchMock(),
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

describe("TermAutoSuggest", () => {
  let container: HTMLDivElement;
  let root: Root;
  const onChange = vi.fn();
  const onSelect = vi.fn();
  const onCreateNew = vi.fn();

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
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
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      false;
  });

  const renderComponent = async (props = {}) => {
    await act(async () => {
      root.render(
        <TermAutoSuggest
          value=""
          onChange={onChange}
          onSelect={onSelect}
          onCreateNew={onCreateNew}
          {...props}
        />
      );
    });
  };

  it("renders input with placeholder", async () => {
    await renderComponent({ placeholder: "Type to search..." });

    const input = container.querySelector('input[type="text"]') as HTMLInputElement | null;
    expect(input).not.toBeNull();
    expect(input?.placeholder).toBe("Type to search...");
  });

  it("shows dropdown when typing 2+ characters and results exist", async () => {
    useVocabularySearchMock.mockReturnValueOnce({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            id: 1,
            term: "protocol",
            language: "en",
            parent_id: null,
            cefr_level: "B2",
            jlpt_level: null,
            part_of_speech: "noun",
            definitions: [],
            created_at: null,
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    });

    await renderComponent({ value: "pro" });

    const dropdown = container.querySelector('[role="listbox"]');
    expect(dropdown).not.toBeNull();
    expect(container.textContent).toContain("protocol");
  });

  it("shows add new term option when no results", async () => {
    useVocabularySearchMock.mockReturnValueOnce({
      isLoading: false,
      isError: false,
      data: {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    });

    await renderComponent({ value: "xyz" });

    expect(container.textContent).toContain('Add "xyz" as new term');
  });

  it("calls onSelect when suggestion is clicked", async () => {
    const mockTerm = {
      id: 1,
      term: "protocol",
      language: "en",
      parent_id: null,
      cefr_level: "B2",
      jlpt_level: null,
      part_of_speech: "noun",
      definitions: [],
      created_at: null,
    };

    useVocabularySearchMock.mockReturnValueOnce({
      isLoading: false,
      isError: false,
      data: {
        items: [mockTerm],
        total: 1,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    });

    await renderComponent({ value: "pro" });

    const option = container.querySelector('[role="option"]');
    await act(async () => {
      option?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(onSelect).toHaveBeenCalledWith(mockTerm);
  });

  it("calls onCreateNew when add new term is clicked", async () => {
    useVocabularySearchMock.mockReturnValueOnce({
      isLoading: false,
      isError: false,
      data: {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    });

    await renderComponent({ value: "newterm" });

    const addOption = container.querySelector('[role="listbox"] + div') as HTMLDivElement | null;
    await act(async () => {
      addOption?.click();
    });

    expect(onCreateNew).toHaveBeenCalled();
  });

  it("displays CEFR and JLPT badges for suggestions", async () => {
    useVocabularySearchMock.mockReturnValueOnce({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            id: 1,
            term: "protocol",
            language: "en",
            parent_id: null,
            cefr_level: "B2",
            jlpt_level: "N1",
            part_of_speech: "noun",
            definitions: [],
            created_at: null,
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    });

    await renderComponent({ value: "pro" });

    expect(container.textContent).toContain("B2");
    expect(container.textContent).toContain("N1");
  });
});