"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { srsKeys } from "@/lib/query-keys";
import type { QueueMode, ReviewRequest, ReviewResponse } from "@/types/srs";

export function useRatingMutation(queueMode: QueueMode) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      cardId,
      data,
    }: {
      cardId: number;
      data: ReviewRequest;
    }) =>
      apiClient<ReviewResponse>(`/srs_cards/${cardId}/review`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: srsKeys.queue(queueMode) });
      queryClient.invalidateQueries({ queryKey: srsKeys.queueStats() });
    },
  });
}
