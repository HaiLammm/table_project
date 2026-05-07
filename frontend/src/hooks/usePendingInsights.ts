"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { diagnosticsKeys } from "@/lib/query-keys";
import type { PendingInsightsResponse } from "@/types/diagnostics";

export function usePendingInsights(sessionId: string | null, enabled: boolean) {
  const apiClient = useApiClient();

  return useQuery({
    queryKey: diagnosticsKeys.pendingInsights(sessionId ?? "pending"),
    queryFn: () => {
      const params = new URLSearchParams({ session_id: sessionId ?? "", limit: "3" });
      return apiClient<PendingInsightsResponse>(`/diagnostics/insights?${params.toString()}`);
    },
    enabled: enabled && sessionId !== null,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  });
}
