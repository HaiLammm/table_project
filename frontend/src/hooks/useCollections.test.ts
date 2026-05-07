import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { collectionKeys } from "@/lib/query-keys";

import { useRemoveTermFromCollection } from "./useCollections";

const useApiClientMock = vi.fn();
const useMutationMock = vi.fn();
const useQueryClientMock = vi.fn();

vi.mock("@/lib/api-client", () => ({
  useApiClient: () => useApiClientMock(),
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation: (options: unknown) => useMutationMock(options),
  useQueryClient: () => useQueryClientMock(),
  useQuery: vi.fn(),
}));

describe("useRemoveTermFromCollection", () => {
  const cache = new Map<string, unknown>();
  const rawKeys = new Map<string, readonly unknown[]>();
  const cancelQueriesMock = vi.fn();
  const invalidateQueriesMock = vi.fn();

  function setCache(key: readonly unknown[], value: unknown) {
    const serialized = JSON.stringify(key);
    rawKeys.set(serialized, key);
    cache.set(serialized, value);
  }

  function getCache(key: readonly unknown[]) {
    return cache.get(JSON.stringify(key));
  }

  beforeEach(() => {
    cache.clear();
    rawKeys.clear();

    useApiClientMock.mockReturnValue(vi.fn());
    useQueryClientMock.mockReturnValue({
      cancelQueries: cancelQueriesMock,
      invalidateQueries: invalidateQueriesMock,
      getQueryData: (key: readonly unknown[]) => getCache(key),
      getQueriesData: ({ queryKey }: { queryKey: readonly unknown[] }) =>
        Array.from(rawKeys.entries())
          .filter(([, key]) => queryKey.every((part, index) => key[index] === part))
          .map(([serialized, key]) => [key, cache.get(serialized)]),
      setQueryData: (key: readonly unknown[], value: unknown) => {
        setCache(key, value);
      },
    });
    useMutationMock.mockImplementation((options) => options);

    setCache(collectionKeys.list(), {
      items: [
        {
          id: 1,
          name: "Backend",
          icon: "💻",
          term_count: 2,
          mastery_percent: 50,
          created_at: null,
          updated_at: null,
        },
      ],
    });
    setCache(collectionKeys.detail(1), {
      id: 1,
      name: "Backend",
      icon: "💻",
      term_count: 2,
      mastery_percent: 50,
      created_at: null,
      updated_at: null,
    });
    setCache([...collectionKeys.terms(1), 1], {
      items: [
        {
          term_id: 10,
          term: "protocol",
          language: "en",
          mastery_status: "learning",
          added_at: null,
          cefr_level: "B2",
          jlpt_level: null,
          part_of_speech: "noun",
        },
        {
          term_id: 11,
          term: "deploy",
          language: "en",
          mastery_status: "new",
          added_at: null,
          cefr_level: null,
          jlpt_level: null,
          part_of_speech: "verb",
        },
      ],
      total: 2,
      page: 1,
      page_size: 20,
      has_next: false,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("optimistically removes a term and restores the cache on error", async () => {
    const mutation = useRemoveTermFromCollection(1) as {
      onMutate?: (termId: number) => Promise<unknown>;
      onError?: (error: Error, termId: number, context: unknown) => void;
    };

    const context = await mutation.onMutate?.(10);

    expect(getCache(collectionKeys.list())).toEqual({
      items: [
        {
          id: 1,
          name: "Backend",
          icon: "💻",
          term_count: 1,
          mastery_percent: 50,
          created_at: null,
          updated_at: null,
        },
      ],
    });
    expect(getCache(collectionKeys.detail(1))).toEqual({
      id: 1,
      name: "Backend",
      icon: "💻",
      term_count: 1,
      mastery_percent: 50,
      created_at: null,
      updated_at: null,
    });
    expect(getCache([...collectionKeys.terms(1), 1])).toEqual({
      items: [
        {
          term_id: 11,
          term: "deploy",
          language: "en",
          mastery_status: "new",
          added_at: null,
          cefr_level: null,
          jlpt_level: null,
          part_of_speech: "verb",
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      has_next: false,
    });

    mutation.onError?.(new Error("rollback"), 10, context);

    expect(getCache(collectionKeys.list())).toEqual({
      items: [
        {
          id: 1,
          name: "Backend",
          icon: "💻",
          term_count: 2,
          mastery_percent: 50,
          created_at: null,
          updated_at: null,
        },
      ],
    });
    expect(getCache(collectionKeys.detail(1))).toEqual({
      id: 1,
      name: "Backend",
      icon: "💻",
      term_count: 2,
      mastery_percent: 50,
      created_at: null,
      updated_at: null,
    });
    expect(getCache([...collectionKeys.terms(1), 1])).toEqual({
      items: [
        {
          term_id: 10,
          term: "protocol",
          language: "en",
          mastery_status: "learning",
          added_at: null,
          cefr_level: "B2",
          jlpt_level: null,
          part_of_speech: "noun",
        },
        {
          term_id: 11,
          term: "deploy",
          language: "en",
          mastery_status: "new",
          added_at: null,
          cefr_level: null,
          jlpt_level: null,
          part_of_speech: "verb",
        },
      ],
      total: 2,
      page: 1,
      page_size: 20,
      has_next: false,
    });
  });
});
