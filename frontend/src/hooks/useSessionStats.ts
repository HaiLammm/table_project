"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { srsKeys } from "@/lib/query-keys";
import type { SessionStatsResponse } from "@/types/srs";

export function useSessionStats(sessionId: string | null, enabled: boolean) {
  const apiClient = useApiClient();

  return useQuery({
    queryKey: srsKeys.sessionStats(sessionId ?? ""),
    queryFn: () =>
      apiClient<SessionStatsResponse>(
        `/srs_cards/session-stats?session_id=${encodeURIComponent(sessionId!)}`,
      ),
    enabled: enabled && sessionId !== null,
  });
}