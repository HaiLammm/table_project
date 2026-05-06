"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { srsKeys } from "@/lib/query-keys";
import type { QueueStatsResponse } from "@/types/srs";

export function useQueueStats() {
  const apiClient = useApiClient();

  return useQuery({
    queryKey: srsKeys.queueStats(),
    queryFn: () => apiClient<QueueStatsResponse>("/srs_cards/queue-stats"),
  });
}
