"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { vocabularyKeys } from "@/lib/query-keys";
import type { PaginatedTermsResponse } from "@/types/vocabulary";

function useDebounce(value: string, delay: number): string {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function useVocabularySearch(query: string) {
  const client = useApiClient();
  const debouncedQuery = useDebounce(query, 200);

  return useQuery({
    queryKey: vocabularyKeys.search(debouncedQuery),
    queryFn: async () => {
      const params = new URLSearchParams({ query: debouncedQuery });
      return client<PaginatedTermsResponse>(
        `/vocabulary_terms/search?${params.toString()}`
      );
    },
    enabled: debouncedQuery.length >= 2,
  });
}
