"use client";

import { type ReactNode, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import { CSVImporter } from "@/components/vocabulary/CSVImporter";
import { CSVPreview } from "@/components/vocabulary/CSVPreview";
import { useCSVImportPreview } from "@/hooks/useCSVImport";
import {
  useAddTermToCollection,
  useAddTermsBulk,
  useImportCSVToCollection,
} from "@/hooks/useCollections";
import { useVocabularySearch } from "@/hooks/useVocabularySearch";
import { ApiClientError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { CollectionCSVImportResponse } from "@/types/collection";
import type { CSVImportPreviewResponse, VocabularyTerm } from "@/types/vocabulary";

type DialogTab = "manual" | "csv" | "browse";

interface AddWordsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  collectionId: number;
  collectionName: string;
}

function getErrorMessage(error: unknown) {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong";
}

function TermResultRow({
  term,
  trailing,
  onClick,
}: {
  term: VocabularyTerm;
  trailing?: ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center justify-between gap-3 rounded-[10px] border border-zinc-200 bg-white px-4 py-3 text-left transition hover:border-zinc-300 hover:bg-zinc-50"
    >
      <div className="min-w-0 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-zinc-900">{term.term}</span>
          <span className="text-xs uppercase tracking-wide text-zinc-500">{term.language}</span>
          {term.part_of_speech ? (
            <span className="text-xs text-zinc-500">{term.part_of_speech}</span>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {term.cefr_level ? <Badge variant="outline">{term.cefr_level}</Badge> : null}
          {term.jlpt_level ? <Badge variant="outline">{term.jlpt_level}</Badge> : null}
        </div>
      </div>
      {trailing}
    </button>
  );
}

function ImportSummary({
  result,
  onReset,
}: {
  result: CollectionCSVImportResponse;
  onReset: () => void;
}) {
  return (
    <div className="space-y-4 rounded-[14px] border border-zinc-200 bg-zinc-50 p-4">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-zinc-900">Import complete</h3>
        <p className="text-sm text-zinc-600">Review the collection import result below.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-[10px] border border-zinc-200 bg-white p-3">
          <p className="text-xs uppercase tracking-wide text-zinc-500">Added</p>
          <p className="mt-1 text-2xl font-semibold text-zinc-900">{result.added}</p>
        </div>
        <div className="rounded-[10px] border border-zinc-200 bg-white p-3">
          <p className="text-xs uppercase tracking-wide text-zinc-500">Skipped</p>
          <p className="mt-1 text-2xl font-semibold text-zinc-900">{result.skipped}</p>
        </div>
        <div className="rounded-[10px] border border-zinc-200 bg-white p-3">
          <p className="text-xs uppercase tracking-wide text-zinc-500">Errors</p>
          <p className="mt-1 text-2xl font-semibold text-zinc-900">{result.errors.length}</p>
        </div>
      </div>

      {result.errors.length > 0 ? (
        <div className="rounded-[10px] border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <p className="font-medium">Some rows could not be matched to existing vocabulary terms.</p>
          <ul className="mt-2 space-y-1">
            {result.errors.slice(0, 5).map((error) => (
              <li key={`${error.row}-${error.error}`}>
                Row {error.row}: {error.error}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <Button type="button" variant="outline" onClick={onReset}>
        Import another file
      </Button>
    </div>
  );
}

export function AddWordsDialog({
  open,
  onOpenChange,
  collectionId,
  collectionName,
}: AddWordsDialogProps) {
  const toast = useToast();
  const addTerm = useAddTermToCollection(collectionId);
  const addTermsBulk = useAddTermsBulk(collectionId);
  const importPreview = useCSVImportPreview();
  const importCSV = useImportCSVToCollection(collectionId);

  const [activeTab, setActiveTab] = useState<DialogTab>("manual");
  const [manualQuery, setManualQuery] = useState("");
  const [browseQuery, setBrowseQuery] = useState("");
  const [manualDuplicateWarning, setManualDuplicateWarning] = useState<string | null>(null);
  const [selectedTermIds, setSelectedTermIds] = useState<Set<number>>(new Set());
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [csvPreview, setCsvPreview] = useState<CSVImportPreviewResponse | null>(null);
  const [csvResult, setCsvResult] = useState<CollectionCSVImportResponse | null>(null);
  const [activeManualIndex, setActiveManualIndex] = useState(0);

  const manualSearch = useVocabularySearch(manualQuery);
  const browseSearch = useVocabularySearch(browseQuery);
  const manualSuggestions = useMemo(() => manualSearch.data?.items ?? [], [manualSearch.data]);
  const browseSuggestions = useMemo(() => browseSearch.data?.items ?? [], [browseSearch.data]);

  function resetDialogState() {
    setActiveTab("manual");
    setManualQuery("");
    setBrowseQuery("");
    setManualDuplicateWarning(null);
    setSelectedTermIds(new Set());
    setSelectedFile(null);
    setCsvPreview(null);
    setCsvResult(null);
    setActiveManualIndex(0);
  }

  async function handleAddSingleTerm(term: VocabularyTerm) {
    setManualDuplicateWarning(null);

    try {
      const result = await addTerm.mutateAsync({ term_id: term.id });
      setManualQuery("");
      toast.success(`Added ${result.added} term to ${collectionName}`);
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 409) {
        setManualDuplicateWarning("Already in collection");
        return;
      }

      toast.error(getErrorMessage(error));
    }
  }

  async function handleAddSelectedTerms() {
    const termIds = Array.from(selectedTermIds);
    if (termIds.length === 0) {
      return;
    }

    try {
      const result = await addTermsBulk.mutateAsync({ term_ids: termIds });
      setSelectedTermIds(new Set());
      toast.success(`Added ${result.added} terms, skipped ${result.skipped}`);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  }

  async function handleSelectCSVFile(file: File) {
    setSelectedFile(file);
    setCsvResult(null);

    try {
      const preview = await importPreview.mutateAsync(file);
      setCsvPreview(preview);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  }

  async function handleImportCSV() {
    if (selectedFile === null) {
      return;
    }

    try {
      const result = await importCSV.mutateAsync(selectedFile);
      setCsvPreview(null);
      setCsvResult(result);
      toast.success(`Added ${result.added} terms from CSV`);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  }

  function toggleSelectedTerm(termId: number) {
    setSelectedTermIds((current) => {
      const next = new Set(current);
      if (next.has(termId)) {
        next.delete(termId);
      } else {
        next.add(termId);
      }
      return next;
    });
  }

  function renderManualTab() {
    return (
      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="manual-term-search" className="text-sm font-medium text-zinc-200">
            Search the corpus
          </label>
          <input
            id="manual-term-search"
            value={manualQuery}
            onChange={(event) => {
              setManualQuery(event.target.value);
              setManualDuplicateWarning(null);
              setActiveManualIndex(0);
            }}
            onKeyDown={(event) => {
              if (manualSuggestions.length === 0) {
                return;
              }

              if (event.key === "ArrowDown") {
                event.preventDefault();
                setActiveManualIndex((current) => Math.min(current + 1, manualSuggestions.length - 1));
                return;
              }

              if (event.key === "ArrowUp") {
                event.preventDefault();
                setActiveManualIndex((current) => Math.max(current - 1, 0));
                return;
              }

              if (event.key === "Enter") {
                event.preventDefault();
                void handleAddSingleTerm(manualSuggestions[activeManualIndex] ?? manualSuggestions[0]);
              }
            }}
            placeholder="Type at least 2 characters"
            className="w-full rounded-[10px] border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-zinc-50 outline-none transition focus:border-zinc-500"
          />
          <p className="text-xs text-zinc-500">
            Press Enter to add the highlighted suggestion to this collection.
          </p>
          {manualDuplicateWarning ? (
            <p className="text-sm text-amber-400">{manualDuplicateWarning}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          {manualSuggestions.map((term, index) => (
            <div
              key={term.id}
              className={cn(
                "rounded-[12px]",
                index === activeManualIndex ? "ring-1 ring-zinc-500" : undefined,
              )}
            >
              <TermResultRow term={term} onClick={() => void handleAddSingleTerm(term)} />
            </div>
          ))}

          {manualQuery.length >= 2 && !manualSearch.isLoading && manualSuggestions.length === 0 ? (
            <div className="rounded-[10px] border border-dashed border-zinc-700 bg-zinc-900/50 px-4 py-6 text-center text-sm text-zinc-400">
              No corpus matches found for this term.
            </div>
          ) : null}
        </div>
      </div>
    );
  }

  function renderBrowseTab() {
    return (
      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="browse-term-search" className="text-sm font-medium text-zinc-200">
            Browse the corpus
          </label>
          <input
            id="browse-term-search"
            value={browseQuery}
            onChange={(event) => setBrowseQuery(event.target.value)}
            placeholder="Search for terms to add in bulk"
            className="w-full rounded-[10px] border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-zinc-50 outline-none transition focus:border-zinc-500"
          />
        </div>

        <div className="space-y-2">
          {browseSuggestions.map((term) => {
            const isSelected = selectedTermIds.has(term.id);
            return (
              <TermResultRow
                key={term.id}
                term={term}
                onClick={() => toggleSelectedTerm(term.id)}
                trailing={
                  <span
                    className={cn(
                      "rounded-full border px-3 py-1 text-xs font-medium",
                      isSelected
                        ? "border-zinc-900 bg-zinc-900 text-zinc-50"
                        : "border-zinc-300 bg-zinc-100 text-zinc-700",
                    )}
                  >
                    {isSelected ? "Selected" : "Select"}
                  </span>
                }
              />
            );
          })}

          {browseQuery.length >= 2 && !browseSearch.isLoading && browseSuggestions.length === 0 ? (
            <div className="rounded-[10px] border border-dashed border-zinc-700 bg-zinc-900/50 px-4 py-6 text-center text-sm text-zinc-400">
              No matching terms were found.
            </div>
          ) : null}
        </div>

        <div className="flex items-center justify-between rounded-[10px] border border-zinc-800 bg-zinc-900/60 px-4 py-3 text-sm text-zinc-400">
          <span>{selectedTermIds.size} selected</span>
          <Button
            type="button"
            onClick={() => void handleAddSelectedTerms()}
            disabled={selectedTermIds.size === 0 || addTermsBulk.isPending}
            className="bg-zinc-100 text-zinc-900 hover:bg-zinc-200"
          >
            {addTermsBulk.isPending ? "Adding..." : "Add Selected"}
          </Button>
        </div>
      </div>
    );
  }

  function renderCSVTab() {
    if (csvResult) {
      return <ImportSummary result={csvResult} onReset={() => setCsvResult(null)} />;
    }

    if (csvPreview) {
      return (
        <CSVPreview
          preview={csvPreview}
          isImporting={importCSV.isPending}
          onImport={() => void handleImportCSV()}
          onCancel={() => {
            setSelectedFile(null);
            setCsvPreview(null);
          }}
        />
      );
    }

    return <CSVImporter onFileSelected={(file) => void handleSelectCSVFile(file)} isLoading={importPreview.isPending} />;
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) {
          resetDialogState();
        }
        onOpenChange(nextOpen);
      }}
    >
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Add Words</DialogTitle>
          <DialogDescription>
            Add existing vocabulary terms to <span className="font-medium text-zinc-200">{collectionName}</span> using manual search, CSV import, or bulk browsing.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-wrap gap-2">
          {([
            ["manual", "Manual"],
            ["csv", "Import CSV"],
            ["browse", "Browse Corpus"],
          ] as const).map(([tab, label]) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={cn(
                "rounded-full border px-4 py-2 text-sm font-medium transition",
                activeTab === tab
                  ? "border-zinc-100 bg-zinc-100 text-zinc-900"
                  : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-zinc-500",
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="max-h-[60vh] overflow-y-auto pr-1">
          {activeTab === "manual" ? renderManualTab() : null}
          {activeTab === "browse" ? renderBrowseTab() : null}
          {activeTab === "csv" ? renderCSVTab() : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
