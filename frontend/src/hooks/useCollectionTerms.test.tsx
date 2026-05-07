// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { collectionKeys } from "@/lib/query-keys";

import { useCollectionTerms } from "./useCollections";

const useApiClientMock = vi.fn();
const useQueryMock = vi.fn();

vi.mock("@/lib/api-client", () => ({
  useApiClient: () => useApiClientMock(),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: (options: unknown) => useQueryMock(options),
  useMutation: vi.fn(),
  useQueryClient: vi.fn(),
}));

function HookHarness({ collectionId, page, search, masteryStatus }: {
  collectionId: number | null;
  page: number;
  search?: string;
  masteryStatus?: string | null;
}) {
  useCollectionTerms(collectionId, page, search, masteryStatus as "new" | "learning" | "mastered" | null | undefined);
  return null;
}

describe("useCollectionTerms", () => {
  let container: HTMLDivElement;
  let root: Root;
  let latestOptions: { queryKey?: unknown; enabled?: boolean; queryFn?: () => Promise<unknown> };

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    vi.useFakeTimers();
    vi.clearAllMocks();
    useApiClientMock.mockReturnValue(vi.fn());
    useQueryMock.mockImplementation((options: unknown) => {
      latestOptions = options as { queryKey?: unknown; enabled?: boolean; queryFn?: () => Promise<unknown> };
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

  it("includes search and mastery_status in query key when provided", async () => {
    await act(async () => {
      root.render(
        <HookHarness collectionId={1} page={2} search="proto" masteryStatus="mastered" />,
      );
    });

    await act(async () => {
      vi.advanceTimersByTime(200);
    });

    expect(latestOptions.queryKey).toEqual([
      "collections",
      1,
      "terms",
      { page: 2, search: "proto", mastery_status: "mastered" },
    ]);
    expect(latestOptions.enabled).toBe(true);
  });

  it("omits search from query key when shorter than 2 chars after debounce", async () => {
    await act(async () => {
      root.render(
        <HookHarness collectionId={1} page={1} search="p" masteryStatus={null} />,
      );
    });

    await act(async () => {
      vi.advanceTimersByTime(200);
    });

    const filters = latestOptions.queryKey as unknown[];
    const filterObj = filters[3] as Record<string, unknown>;
    expect(filterObj.search).toBeUndefined();
    expect(filterObj.mastery_status).toBeUndefined();
  });

  it("disables query when collectionId is null", async () => {
    await act(async () => {
      root.render(
        <HookHarness collectionId={null} page={1} />,
      );
    });

    expect(latestOptions.enabled).toBe(false);
  });
});