type QueueHeaderProps = {
  dueCount: number;
  estimatedMinutes: number;
  retentionRate?: number | null;
};

type StatChipProps = {
  label: string;
  value: string;
};

function StatChip({ label, value }: StatChipProps) {
  return (
    <div className="inline-flex min-h-11 items-center gap-3 rounded-full border border-border bg-secondary/40 px-4 py-2">
      <span className="text-xs font-medium uppercase tracking-[0.12em] text-text-secondary">
        {label}
      </span>
      <span className="text-sm font-semibold text-text-primary">{value}</span>
    </div>
  );
}

export function QueueHeader({ dueCount, estimatedMinutes, retentionRate }: QueueHeaderProps) {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">Today&apos;s Queue</h1>
        <p className="mt-2 text-sm text-text-secondary">
          {dueCount} cards ready. ~{estimatedMinutes} min estimated.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <StatChip label="Ready" value={`${dueCount} cards`} />
        <StatChip label="Estimate" value={`~${estimatedMinutes} min`} />
        {retentionRate !== undefined && retentionRate !== null && (
          <StatChip label="Retention" value={`${Math.round(retentionRate)}%`} />
        )}
      </div>
    </div>
  );
}
