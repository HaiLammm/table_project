"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import { srsKeys } from "@/lib/query-keys";
import type { UpcomingScheduleResponse } from "@/types/srs";

export function useUpcomingSchedule() {
  const apiClient = useApiClient();

  return useQuery({
    queryKey: srsKeys.schedule(),
    queryFn: () => apiClient<UpcomingScheduleResponse>("/srs_cards/schedule"),
  });
}