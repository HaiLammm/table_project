"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useConfirmVocabularyRequest } from "@/hooks/useConfirmVocabularyRequest";
import { useToast } from "@/components/ui/toast";

interface EnrichedTermPreview {
  term_id: number | null;
  candidate_id: string | null;
  term: string;
  language: string;
  definition: string | null;
  ipa: string | null;
  cefr_level: string | null;
  jlpt_level: number | null;
  examples: string[];
  source: string;
  validated_against_jmdict: boolean;
}

interface VocabularyRequestPreviewProps {
  previewData: {
    preview_id: string | null;
    terms: EnrichedTermPreview[];
    corpus_match_count: number;
    gap_count: number;
    requested_count: number;
  };
  onBack: () => void;
}

export function VocabularyRequestPreview({ previewData, onBack }: VocabularyRequestPreviewProps) {
  const router = useRouter();
  const toast = useToast();
  const confirmMutation = useConfirmVocabularyRequest();

  const [selectedCandidateIds, setSelectedCandidateIds] = useState<Set<string>>(
    new Set()
  );
  const [selectedTermIds, setSelectedTermIds] = useState<Set<number>>(
    new Set(previewData.terms.filter((t) => t.term_id !== null).map((t) => t.term_id as number))
  );

  const corpusTerms = previewData.terms.filter((t) => t.source === "corpus");
  const llmTerms = previewData.terms.filter((t) => t.source === "llm");

  const allCorpusSelected = corpusTerms.every(
    (t) => t.term_id !== null && selectedTermIds.has(t.term_id as number)
  );
  const someCorpusSelected = corpusTerms.some(
    (t) => t.term_id !== null && selectedTermIds.has(t.term_id as number)
  );

  const allLlmSelected = llmTerms.every(
    (t) => t.candidate_id !== null && selectedCandidateIds.has(t.candidate_id as string)
  );
  const someLlmSelected = llmTerms.some(
    (t) => t.candidate_id !== null && selectedCandidateIds.has(t.candidate_id as string)
  );

  const toggleCorpusTerm = (id: number) => {
    const newSelected = new Set(selectedTermIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedTermIds(newSelected);
  };

  const toggleLlmTerm = (candidateId: string) => {
    const newSelected = new Set(selectedCandidateIds);
    if (newSelected.has(candidateId)) {
      newSelected.delete(candidateId);
    } else {
      newSelected.add(candidateId);
    }
    setSelectedCandidateIds(newSelected);
  };

  const toggleAllCorpus = () => {
    if (allCorpusSelected) {
      setSelectedTermIds(new Set());
    } else {
      setSelectedTermIds(
        new Set(corpusTerms.filter((t) => t.term_id !== null).map((t) => t.term_id as number))
      );
    }
  };

  const toggleAllLlm = () => {
    if (allLlmSelected) {
      setSelectedCandidateIds(new Set());
    } else {
      setSelectedCandidateIds(
        new Set(llmTerms.filter((t) => t.candidate_id !== null).map((t) => t.candidate_id as string))
      );
    }
  };

  const handleConfirm = () => {
    if (!previewData.preview_id) {
      toast.error("Preview expired. Please generate a new request.");
      return;
    }

    const allSelectedIds = [
      ...Array.from(selectedTermIds).map((id) => `corpus_${id}`),
      ...Array.from(selectedCandidateIds),
    ];

    confirmMutation.mutate(
      {
        preview_id: previewData.preview_id,
        selected_candidate_ids: allSelectedIds,
      },
      {
        onSuccess: (data) => {
          if (data.added_count > 0 && data.skipped_count > 0) {
            toast.success(`${data.added_count} added, ${data.skipped_count} already in your vocabulary`);
          } else if (data.added_count > 0) {
            toast.success(`${data.added_count} terms added to your vocabulary`);
          }
          router.push("/vocabulary");
        },
        onError: () => {
          toast.error("Failed to add terms. Please try again.");
        },
      }
    );
  };

  const totalSelected = selectedTermIds.size + selectedCandidateIds.size;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-text-primary">
            Found {previewData.corpus_match_count} of {previewData.requested_count} terms
          </h3>
          {previewData.gap_count > 0 && llmTerms.length > 0 && (
            <p className="text-sm text-blue-600 mt-1">
              {llmTerms.length} LLM-generated candidates available for review
            </p>
          )}
          {previewData.gap_count > 0 && llmTerms.length === 0 && (
            <p className="text-sm text-orange-600 mt-1">
              Some terms could not be generated. Please try again later.
            </p>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={onBack}>
          Back
        </Button>
      </div>

      {corpusTerms.length > 0 && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={allCorpusSelected}
                onChange={toggleAllCorpus}
                className="w-4 h-4 rounded border-zinc-300"
              />
              <span className="text-sm font-medium text-text-primary">
                Corpus Terms ({corpusTerms.length})
              </span>
            </label>
          </div>

          {corpusTerms.map((term) => (
            <div
              key={`corpus-${term.term_id}`}
              className="flex items-start gap-3 hover:bg-zinc-50 rounded-lg px-3 py-2.5"
            >
              <input
                type="checkbox"
                checked={term.term_id !== null && selectedTermIds.has(term.term_id as number)}
                onChange={() => term.term_id !== null && toggleCorpusTerm(term.term_id as number)}
                disabled={term.term_id === null}
                className="mt-0.5 w-4 h-4 shrink-0 rounded border-zinc-300"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-base font-medium text-text-primary">{term.term}</span>
                  {term.cefr_level && <Badge variant="outline">{term.cefr_level}</Badge>}
                  {term.jlpt_level && <Badge variant="outline">N{term.jlpt_level}</Badge>}
                </div>
                {term.definition && (
                  <p className="mt-1 text-sm text-text-secondary leading-relaxed">{term.definition}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {llmTerms.length > 0 && (
        <div className="flex flex-col gap-2 mt-4 pt-4 border-t border-zinc-200">
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={allLlmSelected}
                onChange={toggleAllLlm}
                className="w-4 h-4 rounded border-zinc-300"
              />
              <span className="text-sm font-medium text-text-primary">
                LLM-Generated Candidates ({llmTerms.length})
              </span>
            </label>
          </div>

          {llmTerms.map((term) => (
            <div
              key={`llm-${term.candidate_id}`}
              className="flex items-start gap-3 hover:bg-zinc-50 rounded-lg px-3 py-2.5"
            >
              <input
                type="checkbox"
                checked={term.candidate_id !== null && selectedCandidateIds.has(term.candidate_id as string)}
                onChange={() => term.candidate_id !== null && toggleLlmTerm(term.candidate_id as string)}
                disabled={term.candidate_id === null}
                className="mt-0.5 w-4 h-4 shrink-0 rounded border-zinc-300"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-base font-medium text-text-primary">{term.term}</span>
                  {term.cefr_level && <Badge variant="outline">{term.cefr_level}</Badge>}
                  {term.jlpt_level && <Badge variant="outline">N{term.jlpt_level}</Badge>}
                  {term.source === "llm" && (
                    <Badge variant="secondary" className="text-xs">AI Generated</Badge>
                  )}
                  {term.validated_against_jmdict && (
                    <Badge variant="outline" className="text-xs text-green-600 border-green-600">
                      JMdict Validated
                    </Badge>
                  )}
                </div>
                {term.definition && (
                  <p className="mt-1 text-sm text-text-secondary leading-relaxed">{term.definition}</p>
                )}
                {term.examples.length > 0 && (
                  <ul className="mt-1.5 space-y-0.5">
                    {term.examples.map((ex, i) => (
                      <li key={i} className="text-xs text-text-tertiary italic">&ldquo;{ex}&rdquo;</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3 pt-4 border-t border-zinc-200">
        <Button
          onClick={handleConfirm}
          disabled={totalSelected === 0 || confirmMutation.isPending}
          className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
        >
          {confirmMutation.isPending
            ? "Adding..."
            : `Add ${totalSelected} Term${totalSelected !== 1 ? "s" : ""}`}
        </Button>
        <Button variant="outline" onClick={onBack}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
