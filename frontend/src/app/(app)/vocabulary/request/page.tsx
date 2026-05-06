"use client";

import { useState } from "react";
import { VocabularyRequestForm } from "@/components/vocabulary/VocabularyRequestForm";
import { VocabularyRequestPreview } from "@/components/vocabulary/VocabularyRequestPreview";
import { Skeleton } from "@/components/ui/skeleton";
import type { VocabularyRequestPreviewResponse } from "@/types/vocabulary";

export default function VocabularyRequestPage() {
  const [previewData, setPreviewData] = useState<VocabularyRequestPreviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handlePreview = (data: VocabularyRequestPreviewResponse) => {
    setPreviewData(data);
    setIsLoading(false);
  };

  const handleBack = () => {
    setPreviewData(null);
  };

  return (
    <section className="mx-auto flex w-full max-w-[720px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-0">
      <div className="space-y-2">
        <h1 className="text-display text-text-primary">Request Vocabulary</h1>
        <p className="text-body text-text-secondary">
          Request a vocabulary set by topic, level, and count
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-32" />
        </div>
      ) : previewData ? (
        <div className="bg-zinc-50 border border-zinc-200 rounded-[10px] p-5">
          <VocabularyRequestPreview previewData={previewData} onBack={handleBack} />
        </div>
      ) : (
        <div className="bg-zinc-50 border border-zinc-200 rounded-[10px] p-5">
          <VocabularyRequestForm onPreview={handlePreview} />
        </div>
      )}
    </section>
  );
}