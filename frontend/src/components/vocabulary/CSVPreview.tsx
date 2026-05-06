"use client";

import { Check, AlertTriangle, X, Loader2 } from "lucide-react";
import type { CSVImportPreviewResponse } from "@/types/vocabulary";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface CSVPreviewProps {
  preview: CSVImportPreviewResponse;
  isImporting?: boolean;
  onImport: () => void;
  onCancel: () => void;
}

export function CSVPreview({
  preview,
  isImporting,
  onImport,
  onCancel,
}: CSVPreviewProps) {
  const getStatusIcon = (status: "valid" | "warning" | "error") => {
    switch (status) {
      case "valid":
        return <Check className="size-4 text-green-600" />;
      case "warning":
        return <AlertTriangle className="size-4 text-amber-500" />;
      case "error":
        return <X className="size-4 text-red-600" />;
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-4 text-sm">
          <span className="text-green-600 font-medium">
            {preview.valid_count} valid
          </span>
          {preview.warning_count > 0 && (
            <span className="text-amber-500 font-medium">
              {preview.warning_count} warnings
            </span>
          )}
          {preview.error_count > 0 && (
            <span className="text-red-600 font-medium">
              {preview.error_count} errors
            </span>
          )}
          <span className="text-zinc-500">
            out of {preview.total_rows} total
          </span>
        </div>
      </div>

      <div className="border border-zinc-200 rounded-[10px] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 border-b border-zinc-200">
              <tr>
                <th className="text-left p-3 font-medium text-zinc-700 w-12">Row</th>
                <th className="text-left p-3 font-medium text-zinc-700">Term</th>
                <th className="text-left p-3 font-medium text-zinc-700 w-20">Language</th>
                <th className="text-left p-3 font-medium text-zinc-700">Definition</th>
                <th className="text-left p-3 font-medium text-zinc-700 w-24">Tags</th>
                <th className="text-left p-3 font-medium text-zinc-700 w-16">Status</th>
              </tr>
            </thead>
            <tbody>
              {preview.preview_rows.map((row) => (
                <tr key={row.row_number} className="border-b border-zinc-100 last:border-0">
                  <td className="p-3 text-zinc-500">{row.row_number}</td>
                  <td className="p-3 font-medium text-zinc-900">
                    {row.term || <span className="text-zinc-400 italic">missing</span>}
                  </td>
                  <td className="p-3 text-zinc-600">{row.language || "en"}</td>
                  <td className="p-3 text-zinc-600 truncate max-w-[200px]">
                    {row.definition || <span className="text-zinc-400">-</span>}
                  </td>
                  <td className="p-3 text-zinc-600 text-xs">
                    {row.tags || <span className="text-zinc-400">-</span>}
                  </td>
                  <td className="p-3">
                    <div className="flex items-center gap-1.5">
                      {getStatusIcon(row.status)}
                      {row.error_message && (
                        <span className="text-xs text-zinc-500 max-w-[100px] truncate">
                          {row.error_message}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-zinc-500">
          Showing first {preview.preview_rows.length} of {preview.total_rows} rows
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={onCancel} disabled={isImporting}>
            Cancel
          </Button>
          <Button
            onClick={onImport}
            disabled={preview.valid_count === 0 || isImporting}
            className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
          >
            {isImporting ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Importing...
              </>
            ) : (
              `Import ${preview.valid_count} valid records`
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}