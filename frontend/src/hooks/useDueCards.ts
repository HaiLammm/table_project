"use client";

import { useMemo } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { srsKeys, vocabularyKeys } from "@/lib/query-keys";
import type { DueCardsResponse, QueueMode, SessionCard } from "@/types/srs";
import type { VocabularyTerm } from "@/types/vocabulary";

export function useDueCards(mode: QueueMode, enabled: boolean) {
  const apiClient = useApiClient();

  const queueQuery = useQuery({
    queryKey: srsKeys.queue(mode),
    queryFn: () => {
      const params = new URLSearchParams({ mode });
      return apiClient<DueCardsResponse>(`/srs_cards/queue?${params.toString()}`);
    },
    enabled,
  });

  const termIds = useMemo(() => {
    if (!queueQuery.data) return [];
    return [...new Set(queueQuery.data.items.map((c) => c.term_id).filter(Boolean))] as number[];
  }, [queueQuery.data]);

  const termQueries = useQueries({
    queries: termIds.map((id: number) => ({
      queryKey: vocabularyKeys.detail(id),
      queryFn: () => apiClient<VocabularyTerm>(`/vocabulary_terms/${id}`),
      enabled: queueQuery.isSuccess && termIds.length > 0,
    })),
  });

  const sessionCards = useMemo((): SessionCard[] => {
    if (!queueQuery.data) return [];
    const termMap = new Map<number, VocabularyTerm>();
    termQueries.forEach((q) => {
      if (q.data) termMap.set(q.data.id, q.data);
    });

    return queueQuery.data.items.map((card) => ({
      ...card,
      term: card.term_id ? (termMap.get(card.term_id) ?? null) : null,
    }));
  }, [queueQuery.data, termQueries]);

  const isTermLoading = termQueries.some((q) => q.isLoading);

  return {
    ...queueQuery,
    sessionCards,
    isLoading: queueQuery.isLoading || (queueQuery.isSuccess && isTermLoading),
  };
}
