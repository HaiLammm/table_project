"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";

import { CatchUpBanner, QueueHeader, UpcomingSchedule } from "@/components/review";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useApiClient } from "@/lib/api-client";
import { srsKeys } from "@/lib/query-keys";
import { useUpcomingSchedule } from "@/hooks/useUpcomingSchedule";
import { useReviewStore } from "@/stores/review-store";

type QueueMode = "full" | "catchup";

type QueueStatsResponse = {
  due_count: number;
  estimated_minutes: number;
  has_overdue: boolean;
  overdue_count: number;
};

type DueCardResponse = {
  id: number;
  term_id: number | null;
  due_at: string;
  fsrs_state: Record<string, unknown>;
};

type DueCardsResponse = {
  items: DueCardResponse[];
  total_count: number;
  limit: number;
  offset: number;
  mode: QueueMode;
};

function useQueueStats() {
  const apiClient = useApiClient();

  return useQuery({
    queryKey: srsKeys.queueStats(),
    queryFn: () => apiClient<QueueStatsResponse>("/srs_cards/queue-stats"),
  });
}

function useDueQueue(mode: QueueMode, enabled: boolean) {
  const apiClient = useApiClient();

  return useQuery({
    queryKey: srsKeys.queue(mode),
    queryFn: () => {
      const params = new URLSearchParams({ mode });
      if (mode === "catchup") {
        params.set("limit", "30");
      }

      return apiClient<DueCardsResponse>(`/srs_cards/queue?${params.toString()}`);
    },
    enabled,
  });
}

function formatDueAt(dueAt: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(dueAt));
}

function QueuePreview({ queue }: { queue: DueCardsResponse }) {
  const title = queue.mode === "catchup" ? "Catch-up queue" : "Due queue";
  const description =
    queue.mode === "catchup"
      ? `Showing the ${queue.items.length} most overdue cards first.`
      : `Showing ${queue.items.length} due cards sorted by due date.`;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {queue.items.map((card) => (
            <li
              key={card.id}
              className="flex min-h-11 items-center justify-between gap-3 rounded-xl border border-border bg-secondary/30 px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-text-primary">Card #{card.id}</p>
                <p className="text-xs text-text-secondary">
                  {card.term_id ? `Term #${card.term_id}` : "Waiting for vocabulary term mapping"}
                </p>
              </div>
              <span className="text-xs text-text-secondary">Due {formatDueAt(card.due_at)}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const queueMode = useReviewStore((state) => state.queueMode);
  const setQueueMode = useReviewStore((state) => state.setQueueMode);
  const queueStatsQuery = useQueueStats();
  const scheduleQuery = useUpcomingSchedule();
  const dueCount = queueStatsQuery.data?.due_count ?? 0;
  const queueQuery = useDueQueue(queueMode, queueStatsQuery.isSuccess && dueCount > 0);

  if (queueStatsQuery.isLoading) {
    return (
      <section className="mx-auto flex min-h-[60vh] w-full max-w-[720px] flex-col justify-center gap-4 px-4 py-6 sm:px-6 lg:px-0">
        <Card>
          <CardContent className="space-y-3 py-6">
            <div className="h-6 w-48 animate-pulse rounded-full bg-muted" />
            <div className="h-4 w-64 animate-pulse rounded-full bg-muted" />
          </CardContent>
        </Card>
      </section>
    );
  }

  if (queueStatsQuery.isError || queueStatsQuery.data === undefined) {
    return (
      <section className="mx-auto flex min-h-[60vh] w-full max-w-[720px] items-center px-4 py-6 sm:px-6 lg:px-0">
        <Card className="w-full">
          <CardHeader>
            <CardTitle>Unable to load today&apos;s queue</CardTitle>
            <CardDescription>
              We couldn&apos;t fetch your current review queue. Please refresh and try again.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (queueStatsQuery.data.due_count === 0) {
    return (
      <section className="mx-auto flex min-h-[70vh] w-full max-w-[720px] flex-col items-center justify-center px-4 py-6 text-center sm:px-6 lg:px-0">
        <CheckCircle2 className="size-10 text-zinc-400" />
        <h1 className="mt-5 text-lg font-semibold text-text-primary">All caught up!</h1>
        <p className="mt-2 max-w-md text-sm text-text-secondary">
          No cards due for review. Come back tomorrow or add new words.
        </p>
        <Button asChild className="mt-6">
          <Link href="/collections">Add Words</Link>
        </Button>
      </section>
    );
  }

  return (
    <section className="mx-auto flex w-full max-w-[720px] flex-col gap-4 px-4 py-6 sm:px-6 lg:px-0">
      <Card>
        <CardContent className="py-6">
          <QueueHeader
            dueCount={queueStatsQuery.data.due_count}
            estimatedMinutes={queueStatsQuery.data.estimated_minutes}
          />
          {scheduleQuery.isSuccess && scheduleQuery.data ? (
            <div className="mt-4">
              <UpcomingSchedule
                tomorrow={scheduleQuery.data.tomorrow}
                thisWeek={scheduleQuery.data.this_week}
                isLoading={scheduleQuery.isLoading}
              />
            </div>
          ) : null}
        </CardContent>
      </Card>

      {queueStatsQuery.data.overdue_count >= 100 ? (
        <CatchUpBanner
          overdueCount={queueStatsQuery.data.overdue_count}
          queueMode={queueMode}
          onStartCatchUp={() => setQueueMode("catchup")}
          onReviewAll={() => setQueueMode("full")}
        />
      ) : null}

      {queueQuery.isLoading ? (
        <Card>
          <CardContent className="space-y-3 py-6">
            <div className="h-4 w-36 animate-pulse rounded-full bg-muted" />
            <div className="h-16 w-full animate-pulse rounded-2xl bg-muted" />
            <div className="h-16 w-full animate-pulse rounded-2xl bg-muted" />
          </CardContent>
        </Card>
      ) : null}

      {queueQuery.isSuccess ? <QueuePreview queue={queueQuery.data} /> : null}
    </section>
  );
}
