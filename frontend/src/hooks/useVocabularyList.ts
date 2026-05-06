"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { vocabularyKeys } from "@/lib/query-keys";
import type { PaginatedTermsResponse, VocabularyFilterParams } from "@/types/vocabulary";

export function useVocabularyList(filters: VocabularyFilterParams = {}) {
  const client = useApiClient();

  return useQuery({
    queryKey: vocabularyKeys.list(filters as Record<string, unknown>),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.page !== undefined) params.set("page", String(filters.page));
      if (filters.page_size !== undefined) params.set("page_size", String(filters.page_size));
      if (filters.cefr_level) params.set("cefr_level", filters.cefr_level);
      if (filters.jlpt_level) params.set("jlpt_level", filters.jlpt_level);
      if (filters.parent_id !== undefined) params.set("parent_id", String(filters.parent_id));

      return client<PaginatedTermsResponse>(
        `/vocabulary_terms?${params.toString()}`
      );
    },
  });
}
