"use client";

import { useState, useRef } from "react";
import { TermAutoSuggest } from "./TermAutoSuggest";
import { Button } from "@/components/ui/button";
import { useCreateVocabularyTerm } from "@/hooks/useCreateVocabularyTerm";
import { useToast } from "@/components/ui/toast";
import { ApiClientError } from "@/lib/api-client";
import type { VocabularyTerm } from "@/types/vocabulary";

interface AddTermFormProps {
  onTermCreated?: (term: VocabularyTerm) => void;
}

export function AddTermForm({ onTermCreated }: AddTermFormProps) {
  const [term, setTerm] = useState("");
  const [language, setLanguage] = useState<"en" | "jp">("en");
  const [showDefinition, setShowDefinition] = useState(false);
  const [definition, setDefinition] = useState("");
  const [error, setError] = useState<string | null>(null);
  const termInputRef = useRef<HTMLInputElement>(null);

  const createTerm = useCreateVocabularyTerm();
  const toast = useToast();

  const handleSelectExisting = (existingTerm: VocabularyTerm) => {
    toast.success("Term added to your vocabulary");
    if (onTermCreated) {
      onTermCreated(existingTerm);
    }
  };

  const handleCreateNew = () => {
    if (!term.trim()) return;

    createTerm.mutate(
      { term: term.trim(), language, definition: definition.trim() || undefined },
      {
        onSuccess: (createdTerm) => {
          toast.success("Term added — enriching...");
          setTerm("");
          setDefinition("");
          setError(null);
          termInputRef.current?.focus();
          if (onTermCreated) {
            onTermCreated(createdTerm);
          }
        },
        onError: (err) => {
          if (err instanceof ApiClientError && err.code === "DUPLICATE_TERM") {
            setError("This term already exists in your vocabulary");
          } else {
            toast.error("Failed to add term. Please try again.");
          }
        },
      }
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!term.trim()) return;
    handleCreateNew();
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="term-input" className="text-sm font-medium text-zinc-700 mb-1.5">
          Term
        </label>
        <TermAutoSuggest
          value={term}
          onChange={(val) => {
            setTerm(val);
            setError(null);
          }}
          onSelect={handleSelectExisting}
          onCreateNew={handleCreateNew}
          placeholder="Type a term to add..."
        />
        {error && <p className="text-red-600 text-sm mt-1">{error}</p>}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="language-select" className="text-sm font-medium text-zinc-700 mb-1.5">
          Language
        </label>
        <select
          id="language-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value as "en" | "jp")}
          className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10"
        >
          <option value="en">English</option>
          <option value="jp">Japanese</option>
        </select>
      </div>

      {!showDefinition && (
        <button
          type="button"
          onClick={() => setShowDefinition(true)}
          className="text-sm text-zinc-500 hover:text-zinc-700 transition text-left"
        >
          + Add definition (optional)
        </button>
      )}

      {showDefinition && (
        <div className="flex flex-col gap-1.5">
          <label htmlFor="definition-input" className="text-sm font-medium text-zinc-700 mb-1.5">
            Definition
          </label>
          <textarea
            id="definition-input"
            value={definition}
            onChange={(e) => setDefinition(e.target.value)}
            placeholder="Enter a definition (optional)"
            rows={3}
            className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10 resize-none"
          />
        </div>
      )}

      <Button
        type="submit"
        disabled={!term.trim() || createTerm.isPending}
        className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800 self-start"
      >
        {createTerm.isPending ? "Adding..." : "Add Term"}
      </Button>
    </form>
  );
}