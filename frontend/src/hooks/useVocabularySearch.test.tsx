// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { vocabularyKeys } from "@/lib/query-keys";

import { useVocabularySearch } from "./useVocabularySearch";

const useApiClientMock = vi.fn();
const useQueryMock = vi.fn();

vi.mock("@/lib/api-client", () => ({
  useApiClient: () => useApiClientMock(),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: (options: unknown) => useQueryMock(options),
}));

function HookHarness({ query }: { query: string }) {
  useVocabularySearch(query);
  return null;
}

describe("useVocabularySearch", () => {
  let container: HTMLDivElement;
  let root: Root;
  let latestOptions: { queryKey?: unknown; enabled?: boolean };

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    vi.useFakeTimers();
    vi.clearAllMocks();
    useApiClientMock.mockReturnValue(vi.fn());
    useQueryMock.mockImplementation((options: unknown) => {
      latestOptions = options as { queryKey?: unknown; enabled?: boolean };
      return { data: undefined, isLoading: false, isError: false };
    });
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    vi.useRealTimers();
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  });

  it("debounces search queries by 200ms before enabling the request", async () => {
    await act(async () => {
      root.render(<HookHarness query="" />);
    });

    expect(latestOptions.queryKey).toEqual(vocabularyKeys.search(""));
    expect(latestOptions.enabled).toBe(false);

    await act(async () => {
      root.render(<HookHarness query="protocol" />);
    });

    expect(latestOptions.queryKey).toEqual(vocabularyKeys.search(""));

    await act(async () => {
      vi.advanceTimersByTime(200);
    });

    expect(latestOptions.queryKey).toEqual(vocabularyKeys.search("protocol"));
    expect(latestOptions.enabled).toBe(true);
  });
});
