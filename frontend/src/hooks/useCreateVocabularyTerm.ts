"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { vocabularyKeys } from "@/lib/query-keys";
import type { VocabularyTerm } from "@/types/vocabulary";

export interface VocabularyTermCreateRequest {
  term: string;
  language: "en" | "jp";
  definition?: string;
  cefr_level?: string;
  jlpt_level?: string;
  part_of_speech?: string;
}

export function useCreateVocabularyTerm() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: VocabularyTermCreateRequest) =>
      apiClient<VocabularyTerm>("/vocabulary_terms", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: vocabularyKeys.all });
    },
  });
}