"use client";

import { useMutation } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import type { InsightSeenRequest, InsightSeenResponse } from "@/types/diagnostics";

export function useInsightSeenMutation() {
  const apiClient = useApiClient();

  return useMutation({
    mutationFn: ({
      insightId,
      sessionId,
    }: {
      insightId: number;
      sessionId: string;
    }) =>
      apiClient<InsightSeenResponse>(`/diagnostics/insights/${insightId}/seen`, {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId } satisfies InsightSeenRequest),
      }),
  });
}
