// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import VocabularyTermPage from "./page";

const useApiClientMock = vi.fn();
const useQueryMock = vi.fn();

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ termId: "1" }),
}));

vi.mock("@/lib/api-client", () => ({
  useApiClient: () => useApiClientMock(),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: (options: unknown) => useQueryMock(options),
}));

const mockTerm = {
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
      ipa: "/ˈprɑːtəkɔːl/",
      examples: ["The protocol defines how data is transmitted."],
      source: "seed",
      validated_against_jmdict: true,
    },
    {
      id: 2,
      language: "ja",
      definition: "通信規則の集合",
      ipa: "/pɯotokoːɯ/",
      examples: ["プロトコルは数据传输方法を定義する。"],
      source: "seed",
      validated_against_jmdict: false,
    },
  ],
  created_at: null,
};

describe("VocabularyTermPage", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    useApiClientMock.mockReturnValue(vi.fn());
    sessionStorage.clear();
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

  it("renders term details", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: mockTerm,
    }));

    await act(async () => {
      root.render(<VocabularyTermPage />);
    });

    expect(container.textContent).toContain("protocol");
    expect(container.textContent).toContain("A set of communication rules");
    expect(container.textContent).toContain("B2");
    expect(container.textContent).toContain("/ˈprɑːtəkɔːl/");
  });

  it("renders IPA notation", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: mockTerm,
    }));

    await act(async () => {
      root.render(<VocabularyTermPage />);
    });

    expect(container.textContent).toContain("/ˈprɑːtəkɔːl/");
  });

  it("renders example sentences", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: mockTerm,
    }));

    await act(async () => {
      root.render(<VocabularyTermPage />);
    });

    expect(container.textContent).toContain("The protocol defines how data is transmitted.");
  });

  it("renders parallel toggle button", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: mockTerm,
    }));

    await act(async () => {
      root.render(<VocabularyTermPage />);
    });

    expect(container.textContent).toContain("Single");
  });

  it("shows parallel view with English and Japanese when sessionStorage is set", async () => {
    sessionStorage.setItem("vocabulary_parallel_mode", "true");

    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: mockTerm,
    }));

    await act(async () => {
      root.render(<VocabularyTermPage />);
    });

    await act(async () => {});

    expect(container.textContent).toContain("English");
    expect(container.textContent).toContain("Japanese");
    expect(container.textContent).toContain("通信規則の集合");
  });

  it("shows JMdict warning in parallel mode for unvalidated definitions", async () => {
    sessionStorage.setItem("vocabulary_parallel_mode", "true");

    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: mockTerm,
    }));

    await act(async () => {
      root.render(<VocabularyTermPage />);
    });

    await act(async () => {});

    const svgElements = container.querySelectorAll("svg");
    const amberIcons = Array.from(svgElements).filter((svg) => {
      return svg.getAttribute("class")?.includes("text-amber") ?? false;
    });
    expect(amberIcons.length).toBeGreaterThan(0);
  });

  it("renders loading skeleton", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: true,
      isError: false,
      isSuccess: false,
      data: undefined,
    }));

    await act(async () => {
      root.render(<VocabularyTermPage />);
    });

    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders error state", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: true,
      isSuccess: false,
      data: undefined,
    }));

    await act(async () => {
      root.render(<VocabularyTermPage />);
    });

    expect(container.textContent).toContain("Failed to load term");
  });

  it("renders 404 state when data is undefined", async () => {
    useQueryMock.mockImplementation(() => ({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: undefined,
    }));

    await act(async () => {
      root.render(<VocabularyTermPage />);
    });

    expect(container.textContent).toContain("Term not found");
  });
});
