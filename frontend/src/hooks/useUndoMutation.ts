"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { srsKeys } from "@/lib/query-keys";
import type { QueueMode, ReviewResponse } from "@/types/srs";

export function useUndoMutation(queueMode: QueueMode) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cardId }: { cardId: number }) =>
      apiClient<ReviewResponse>(`/srs_cards/${cardId}/review/undo`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: srsKeys.queue(queueMode) });
      queryClient.invalidateQueries({ queryKey: srsKeys.queueStats() });
    },
  });
}
