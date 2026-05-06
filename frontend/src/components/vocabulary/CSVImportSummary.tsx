"use client";

import Link from "next/link";
import { Check, AlertTriangle, X } from "lucide-react";
import type { CSVImportResultResponse } from "@/types/vocabulary";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface CSVImportSummaryProps {
  result: CSVImportResultResponse;
  onDone: () => void;
}

export function CSVImportSummary({ result, onDone }: CSVImportSummaryProps) {
  return (
    <div className="flex flex-col gap-6">
      <Card className="bg-zinc-50 border border-zinc-200 rounded-[10px] p-6">
        <CardContent className="p-0">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <Check className="size-5 text-green-600" />
              <span className="text-lg font-semibold text-zinc-900">
                Import Complete
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <Check className="size-4 text-green-600" />
                  <span className="text-2xl font-bold text-green-600">
                    {result.imported_count}
                  </span>
                </div>
                <span className="text-sm text-zinc-600">Imported</span>
              </div>

              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="size-4 text-amber-500" />
                  <span className="text-2xl font-bold text-amber-500">
                    {result.review_count}
                  </span>
                </div>
                <span className="text-sm text-zinc-600">Need Review</span>
              </div>

              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <X className="size-4 text-zinc-400" />
                  <span className="text-2xl font-bold text-zinc-400">
                    {result.duplicates_skipped}
                  </span>
                </div>
                <span className="text-sm text-zinc-600">Duplicates Skipped</span>
              </div>
            </div>

            {result.errors.length > 0 && (
              <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-[10px]">
                <p className="text-sm font-medium text-red-700 mb-2">
                  {result.errors.length} error(s) occurred:
                </p>
                <ul className="text-xs text-red-600 space-y-1">
                  {result.errors.slice(0, 5).map((err, idx) => (
                    <li key={idx}>
                      Row {err.row}: {err.error}
                    </li>
                  ))}
                  {result.errors.length > 5 && (
                    <li>...and {result.errors.length - 5} more</li>
                  )}
                </ul>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Link href="/vocabulary">
          <Button variant="outline" className="flex items-center gap-2">
            View imported terms
          </Button>
        </Link>
        <Button
          onClick={onDone}
          className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
        >
          Done
        </Button>
      </div>
    </div>
  );
}