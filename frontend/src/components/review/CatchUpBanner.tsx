import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type CatchUpBannerProps = {
  overdueCount: number;
  queueMode: "full" | "catchup";
  onStartCatchUp: () => void;
  onReviewAll: () => void;
};

export function CatchUpBanner({
  overdueCount,
  queueMode,
  onStartCatchUp,
  onReviewAll,
}: CatchUpBannerProps) {
  if (overdueCount < 100) {
    return null;
  }

  return (
    <Card className="border-border/80 bg-card">
      <CardContent className="flex flex-col gap-4 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-text-primary">
            You have {overdueCount} cards. We suggest starting with the 30 most overdue.
          </p>
          <p className="text-sm text-text-secondary">
            Start smaller if you want an easier way back in, or open the full queue right away.
          </p>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button
            type="button"
            className="bg-zinc-900 text-white hover:bg-zinc-800"
            disabled={queueMode === "catchup"}
            onClick={onStartCatchUp}
          >
            Start catch-up
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={queueMode === "full"}
            onClick={onReviewAll}
          >
            Review all
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
