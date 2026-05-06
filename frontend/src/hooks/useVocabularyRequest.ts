"use client";

import { useMutation } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import {
  type VocabularyRequestCreate,
  type VocabularyRequestPreviewResponse,
} from "@/types/vocabulary";

export function useVocabularyRequest() {
  const apiClient = useApiClient();

  return useMutation({
    mutationFn: (data: VocabularyRequestCreate) =>
      apiClient<VocabularyRequestPreviewResponse>("/vocabulary_requests/preview", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  });
}

export interface VocabularyRequestState {
  previewId: string | null;
  terms: VocabularyRequestPreviewResponse["terms"];
  corpusMatchCount: number;
  gapCount: number;
  requestedCount: number;
}