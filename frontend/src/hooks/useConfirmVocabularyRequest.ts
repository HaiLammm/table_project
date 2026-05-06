"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useApiClient } from "@/lib/api-client";
import { vocabularyKeys } from "@/lib/query-keys";
import type { VocabularyRequestConfirmRequest } from "@/types/vocabulary";

export function useConfirmVocabularyRequest() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (data: VocabularyRequestConfirmRequest) =>
      apiClient<{ added_count: number; skipped_count: number }>("/vocabulary_requests/confirm", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: vocabularyKeys.all });
      if (data.added_count > 0 && data.skipped_count > 0) {
      } else if (data.added_count > 0) {
      }
      router.push("/vocabulary");
    },
  });
}