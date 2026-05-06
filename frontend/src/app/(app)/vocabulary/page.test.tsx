// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import VocabularyPage from "./page";

const useApiClientMock = vi.fn();
const useQueryMock = vi.fn();

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@/lib/api-client", () => ({
  useApiClient: () => useApiClientMock(),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: (options: unknown) => useQueryMock(options),
}));

describe("VocabularyPage", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    useApiClientMock.mockReturnValue(vi.fn());
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      false;
    vi.clearAllMocks();
  });

  it("renders the vocabulary page title", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    }));

    await act(async () => {
      root.render(<VocabularyPage />);
    });

    expect(container.textContent).toContain("Vocabulary");
  });

  it("renders the search bar", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    }));

    await act(async () => {
      root.render(<VocabularyPage />);
    });

    const input = container.querySelector('input[name="query"]');
    expect(input).not.toBeNull();
  });

  it("renders empty state when no items", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    }));

    await act(async () => {
      root.render(<VocabularyPage />);
    });

    expect(container.textContent).toContain("No results found");
  });

  it("renders vocabulary terms", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
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
            definitions: [
              {
                id: 1,
                language: "en",
                definition: "A set of communication rules",
                ipa: null,
                examples: [],
                source: "seed",
                validated_against_jmdict: false,
              },
            ],
            created_at: null,
          },
          {
            id: 2,
            term: "network",
            language: "en",
            parent_id: null,
            cefr_level: "B1",
            jlpt_level: null,
            part_of_speech: "noun",
            definitions: [
              {
                id: 2,
                language: "en",
                definition: "A group of connected devices",
                ipa: null,
                examples: [],
                source: "seed",
                validated_against_jmdict: false,
              },
            ],
            created_at: null,
          },
        ],
        total: 2,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    }));

    await act(async () => {
      root.render(<VocabularyPage />);
    });

    expect(container.textContent).toContain("protocol");
    expect(container.textContent).toContain("network");
    expect(container.textContent).toContain("B2");
    expect(container.textContent).toContain("B1");
  });

  it("renders loading skeletons", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: true,
      isError: false,
      isSuccess: false,
      data: undefined,
    }));

    await act(async () => {
      root.render(<VocabularyPage />);
    });

    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders CEFR and JLPT filter dropdowns", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        has_next: false,
      },
    }));

    await act(async () => {
      root.render(<VocabularyPage />);
    });

    const selects = container.querySelectorAll("select");
    expect(selects.length).toBeGreaterThanOrEqual(2);
  });
});
