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
  const [languages, setLanguages] = useState<Set<"en" | "jp">>(new Set(["en"]));
  const [showDefinition, setShowDefinition] = useState(false);
  const [definitionEn, setDefinitionEn] = useState("");
  const [definitionJp, setDefinitionJp] = useState("");
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

  const toggleLanguage = (lang: "en" | "jp") => {
    setLanguages((prev) => {
      const next = new Set(prev);
      if (next.has(lang)) {
        next.delete(lang);
      } else {
        next.add(lang);
      }
      return next;
    });
  };

  const handleCreateNew = async () => {
    if (!term.trim() || languages.size === 0) return;

    const langs = Array.from(languages);
    const trimmedTerm = term.trim();
    const defByLang: Record<string, string | undefined> = {
      en: definitionEn.trim() || undefined,
      jp: definitionJp.trim() || undefined,
    };

    let lastCreated: VocabularyTerm | null = null;
    let hasError = false;

    for (const lang of langs) {
      try {
        lastCreated = await createTerm.mutateAsync({
          term: trimmedTerm,
          language: lang,
          definition: defByLang[lang],
        });
      } catch (err) {
        if (err instanceof ApiClientError && err.code === "DUPLICATE_TERM") {
          if (langs.length === 1) {
            setError("This term already exists in your vocabulary");
          } else {
            toast.error(`"${trimmedTerm}" (${lang.toUpperCase()}) already exists — skipped`);
          }
        } else {
          toast.error("Failed to add term. Please try again.");
        }
        hasError = true;
      }
    }

    if (lastCreated) {
      const count = langs.length;
      toast.success(count > 1 ? `Term added for ${langs.map((l) => l.toUpperCase()).join(" + ")}` : "Term added — enriching...");
      setTerm("");
      setDefinitionEn("");
      setDefinitionJp("");
      setError(null);
      termInputRef.current?.focus();
      if (onTermCreated) {
        onTermCreated(lastCreated);
      }
    } else if (!hasError) {
      toast.error("Failed to add term. Please try again.");
    }
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

      <fieldset className="flex flex-col gap-1.5">
        <legend className="text-sm font-medium text-zinc-700 mb-1.5">Language</legend>
        <div className="flex gap-2">
          {([["en", "English"], ["jp", "Japanese"]] as const).map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => toggleLanguage(value)}
              className={`rounded-[10px] border px-4 py-2 text-sm font-medium transition ${
                languages.has(value)
                  ? "border-zinc-900 bg-zinc-900 text-zinc-50"
                  : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </fieldset>

      {!showDefinition && (
        <button
          type="button"
          onClick={() => setShowDefinition(true)}
          className="text-sm text-zinc-500 hover:text-zinc-700 transition text-left"
        >
          + Add definition (optional)
        </button>
      )}

      {showDefinition && languages.has("en") && (
        <div className="flex flex-col gap-1.5">
          <label htmlFor="definition-en" className="text-sm font-medium text-zinc-700 mb-1.5">
            Definition (English)
          </label>
          <textarea
            id="definition-en"
            value={definitionEn}
            onChange={(e) => setDefinitionEn(e.target.value)}
            placeholder="Enter English definition (optional)"
            rows={2}
            className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10 resize-none"
          />
        </div>
      )}

      {showDefinition && languages.has("jp") && (
        <div className="flex flex-col gap-1.5">
          <label htmlFor="definition-jp" className="text-sm font-medium text-zinc-700 mb-1.5">
            Definition (Japanese)
          </label>
          <textarea
            id="definition-jp"
            value={definitionJp}
            onChange={(e) => setDefinitionJp(e.target.value)}
            placeholder="Enter Japanese definition (optional)"
            rows={2}
            className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10 resize-none"
          />
        </div>
      )}

      <Button
        type="submit"
        disabled={!term.trim() || languages.size === 0 || createTerm.isPending}
        className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800 self-start"
      >
        {createTerm.isPending ? "Adding..." : "Add Term"}
      </Button>
    </form>
  );
}