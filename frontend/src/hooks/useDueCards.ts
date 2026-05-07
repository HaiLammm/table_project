"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { srsKeys } from "@/lib/query-keys";
import type { DueCardsResponse, QueueMode, SessionCard } from "@/types/srs";

export function useDueCards(mode: QueueMode, enabled: boolean, collectionId?: number) {
  const apiClient = useApiClient();

  const queueQuery = useQuery({
    queryKey: srsKeys.queue(mode, collectionId),
    queryFn: () => {
      const params = new URLSearchParams({ mode });
      if (collectionId !== undefined) {
        params.set("collection_id", String(collectionId));
      }
      return apiClient<DueCardsResponse>(`/srs_cards/queue?${params.toString()}`);
    },
    enabled,
    staleTime: 60_000,
  });

  const sessionCards = useMemo((): SessionCard[] => {
    if (!queueQuery.data) return [];
    return queueQuery.data.items.map((card) => ({
      ...card,
      term: card.term ?? null,
    }));
  }, [queueQuery.data]);

  return {
    ...queueQuery,
    sessionCards,
    isLoading: queueQuery.isLoading,
  };
}
