"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useApiClient } from "@/lib/api-client";
import { srsKeys } from "@/lib/query-keys";
import type { CreateCardsForCollectionResponse, QueueStatsResponse } from "@/types/srs";

export function useStartCollectionReview(collectionId: number) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: () =>
      apiClient<CreateCardsForCollectionResponse>("/srs_cards/cards/create-for-collection", {
        method: "POST",
        body: JSON.stringify({ collection_id: collectionId, language: "en" }),
      }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: srsKeys.queueStats(collectionId) });
      await queryClient.invalidateQueries({ queryKey: srsKeys.queue("full", collectionId) });
      await queryClient.invalidateQueries({ queryKey: srsKeys.queue("catchup", collectionId) });
      await queryClient.invalidateQueries({ queryKey: srsKeys.queueStats() });
      await queryClient.invalidateQueries({ queryKey: srsKeys.queue("full") });
      await queryClient.invalidateQueries({ queryKey: srsKeys.queue("catchup") });

      if (data.created_count > 0) {
        queryClient.setQueryData(["toast-create-cards"], data.created_count);
      }

      const statsResult = await queryClient.fetchQuery({
        queryKey: srsKeys.queueStats(collectionId),
        queryFn: () =>
          apiClient<QueueStatsResponse>(
            `/srs_cards/queue-stats?collection_id=${collectionId}`,
          ),
      });

      if (statsResult.due_count > 0) {
        router.push(`/review?collection=${collectionId}`);
      } else {
        queryClient.setQueryData(["toast-no-cards-due"], true);
      }
    },
  });
}