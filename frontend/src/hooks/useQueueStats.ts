"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { srsKeys } from "@/lib/query-keys";
import type { QueueStatsResponse } from "@/types/srs";

export function useQueueStats(collectionId?: number) {
  const apiClient = useApiClient();

  return useQuery({
    queryKey: srsKeys.queueStats(collectionId),
    queryFn: () => {
      const params = new URLSearchParams();
      if (collectionId !== undefined) {
        params.set("collection_id", String(collectionId));
      }
      const query = params.toString();
      return apiClient<QueueStatsResponse>(`/srs_cards/queue-stats${query ? `?${query}` : ""}`);
    },
    staleTime: 60_000,
  });
}