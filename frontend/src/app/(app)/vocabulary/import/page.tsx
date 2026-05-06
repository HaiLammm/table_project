"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { CSVImporter } from "@/components/vocabulary/CSVImporter";
import { CSVPreview } from "@/components/vocabulary/CSVPreview";
import { CSVImportSummary } from "@/components/vocabulary/CSVImportSummary";
import { useCSVImportPreview, useCSVImport } from "@/hooks/useCSVImport";
import { Button } from "@/components/ui/button";
import type { CSVImportPreviewResponse, CSVImportResultResponse } from "@/types/vocabulary";

type ImportStep = "upload" | "preview" | "summary";

export default function CSVImportPage() {
  const router = useRouter();
  const [step, setStep] = useState<ImportStep>("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<CSVImportPreviewResponse | null>(null);
  const [resultData, setResultData] = useState<CSVImportResultResponse | null>(null);

  const previewMutation = useCSVImportPreview();
  const importMutation = useCSVImport();

  const handleFileSelected = useCallback(
    async (file: File) => {
      setSelectedFile(file);
      try {
        const preview = await previewMutation.mutateAsync(file);
        setPreviewData(preview);
        setStep("preview");
      } catch (error) {
        console.error("Preview failed:", error);
      }
    },
    [previewMutation]
  );

  const handleImport = useCallback(async () => {
    if (!selectedFile) return;

    try {
      const result = await importMutation.mutateAsync(selectedFile);
      setResultData(result);
      setStep("summary");
    } catch (error) {
      console.error("Import failed:", error);
    }
  }, [selectedFile, importMutation]);

  const handleCancel = useCallback(() => {
    setStep("upload");
    setSelectedFile(null);
    setPreviewData(null);
  }, []);

  const handleDone = useCallback(() => {
    router.push("/vocabulary");
  }, [router]);

  return (
    <section className="mx-auto flex w-full max-w-[720px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-0">
      <div className="flex items-center gap-4">
        <Link href="/vocabulary">
          <Button variant="ghost" size="sm" className="gap-1.5">
            <ArrowLeft className="size-4" />
            Back
          </Button>
        </Link>
        <div className="space-y-0.5">
          <h1 className="text-display text-text-primary">Import CSV</h1>
          <p className="text-body text-text-secondary">
            Import vocabulary terms from CSV files
          </p>
        </div>
      </div>

      {step === "upload" && (
        <CSVImporter
          onFileSelected={handleFileSelected}
          isLoading={previewMutation.isPending}
        />
      )}

      {step === "preview" && previewData && (
        <CSVPreview
          preview={previewData}
          isImporting={importMutation.isPending}
          onImport={handleImport}
          onCancel={handleCancel}
        />
      )}

      {step === "summary" && resultData && (
        <CSVImportSummary result={resultData} onDone={handleDone} />
      )}
    </section>
  );
}