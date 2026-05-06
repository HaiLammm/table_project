"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { ApiClientError, useApiClient } from "@/lib/api-client";
import { userKeys } from "@/lib/query-keys";

type DataExportResponse = {
  export_id: number;
  status: "pending" | "processing" | "ready" | "expired" | "failed";
  created_at: string | null;
};

function getErrorMessage(error: unknown) {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to request your data export";
}

export function DataExportButton() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const { success, error: showError } = useToast();

  const requestExportMutation = useMutation({
    mutationFn: () =>
      apiClient<DataExportResponse>("/users/me/data-export", {
        method: "POST",
      }),
    onSuccess: () => {
      success("Export requested. You'll be notified when ready.");
      void queryClient.invalidateQueries({ queryKey: userKeys.dataExport() });
    },
    onError: (mutationError) => {
      showError(getErrorMessage(mutationError));
    },
  });

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-border bg-secondary/30 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-1">
        <h3 className="text-sm font-medium text-text-primary">Export your personal data</h3>
        <p className="text-sm text-text-secondary">
          Generate a ZIP archive of your account profile, preferences, and current learning data.
        </p>
      </div>

      <Button
        type="button"
        variant="outline"
        disabled={requestExportMutation.isPending}
        onClick={() => requestExportMutation.mutate()}
      >
        {requestExportMutation.isPending ? <LoaderCircle className="size-4 animate-spin" /> : null}
        {requestExportMutation.isPending ? "Requesting..." : "Request export"}
      </Button>
    </div>
  );
}
