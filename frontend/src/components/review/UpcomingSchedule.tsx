"use client";

import type { ScheduleBucketResponse } from "@/types/srs";

type UpcomingScheduleProps = {
  tomorrow: ScheduleBucketResponse;
  thisWeek: ScheduleBucketResponse;
  isLoading?: boolean;
};

function StatChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="inline-flex min-h-11 items-center gap-3 rounded-full border border-border bg-secondary/40 px-4 py-2">
      <span className="text-xs font-medium uppercase tracking-[0.12em] text-text-secondary">
        {label}
      </span>
      <span className="text-sm font-semibold text-text-primary">{value}</span>
    </div>
  );
}

function StatChipSkeleton() {
  return (
    <div className="inline-flex min-h-11 w-32 items-center gap-3 rounded-full border border-border bg-secondary/40 px-4 py-2">
      <div className="h-3 w-12 animate-pulse rounded-full bg-muted" />
      <div className="h-4 w-16 animate-pulse rounded-full bg-muted" />
    </div>
  );
}

export function UpcomingSchedule({ tomorrow, thisWeek, isLoading }: UpcomingScheduleProps) {
  if (isLoading) {
    return (
      <div className="flex flex-wrap gap-2">
        <StatChipSkeleton />
        <StatChipSkeleton />
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      <StatChip
        label="Tomorrow"
        value={`${tomorrow.due_count} cards · ~${tomorrow.estimated_minutes} min`}
      />
      <StatChip
        label="This week"
        value={`${thisWeek.due_count} cards · ~${thisWeek.estimated_minutes} min`}
      />
    </div>
  );
}