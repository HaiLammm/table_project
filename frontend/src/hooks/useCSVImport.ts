"use client";

import { useMutation } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import type {
  CSVImportPreviewResponse,
  CSVImportResultResponse,
} from "@/types/vocabulary";

export function useCSVImportPreview() {
  const apiClient = useApiClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      const response = await apiClient<CSVImportPreviewResponse>(
        "/vocabulary_terms/import/preview",
        {
          method: "POST",
          body: formData,
        }
      );

      return response;
    },
  });
}

export function useCSVImport() {
  const apiClient = useApiClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      const response = await apiClient<CSVImportResultResponse>(
        "/vocabulary_terms/import",
        {
          method: "POST",
          body: formData,
        }
      );

      return response;
    },
  });
}