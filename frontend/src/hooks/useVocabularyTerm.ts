"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { vocabularyKeys } from "@/lib/query-keys";
import type { VocabularyTerm } from "@/types/vocabulary";

export function useVocabularyTerm(termId: number) {
  const client = useApiClient();

  return useQuery({
    queryKey: vocabularyKeys.detail(termId),
    queryFn: async () => {
      return client<VocabularyTerm>(`/vocabulary_terms/${termId}`);
    },
  });
}

export function useVocabularyTermChildren(parentId: number) {
  const client = useApiClient();

  return useQuery({
    queryKey: vocabularyKeys.children(parentId),
    queryFn: async () => {
      return client<VocabularyTerm[]>(`/vocabulary_terms/${parentId}/children`);
    },
  });
}
