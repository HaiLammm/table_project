"use client";

import { useCallback, useState } from "react";
import { Upload } from "lucide-react";

interface CSVImporterProps {
  onFileSelected: (file: File) => void;
  isLoading?: boolean;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024;

export function CSVImporter({ onFileSelected, isLoading }: CSVImporterProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback((file: File): string | null => {
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!extension || !["csv", "tsv", "txt"].includes(extension)) {
      return "Only CSV, TSV, and TXT files are accepted";
    }
    if (file.size > MAX_FILE_SIZE) {
      return "File exceeds maximum size of 10MB";
    }
    return null;
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      setError(null);
      onFileSelected(file);
    },
    [onFileSelected, validateFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  return (
    <div className="flex flex-col gap-4">
      <div
        className={`border-2 border-dashed rounded-[10px] p-8 text-center transition-colors ${
          isDragging
            ? "border-zinc-900 bg-zinc-50"
            : "border-zinc-300 hover:border-zinc-400"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".csv,.tsv,.txt"
          onChange={handleInputChange}
          className="hidden"
          id="csv-file-input"
          disabled={isLoading}
        />
        <label
          htmlFor="csv-file-input"
          className={`flex flex-col items-center gap-3 cursor-pointer ${
            isLoading ? "opacity-50 pointer-events-none" : ""
          }`}
        >
          <Upload className="size-10 text-zinc-400" />
          <div className="text-sm">
            <span className="text-zinc-700 font-medium">
              Drop CSV file here or click to browse
            </span>
            <p className="text-zinc-500 mt-1">Supports .csv, .tsv, .txt up to 10MB</p>
          </div>
        </label>
      </div>

      {error && (
        <div className="border-l-4 border-red-500 bg-red-50 p-3 rounded">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center gap-2 text-sm text-zinc-500">
          <div className="size-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900" />
          Parsing file...
        </div>
      )}
    </div>
  );
}