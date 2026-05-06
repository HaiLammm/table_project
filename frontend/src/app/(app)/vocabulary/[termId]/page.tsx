"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertTriangle, ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { LanguageToggle } from "@/components/vocabulary/LanguageToggle";
import { useVocabularyTerm, useVocabularyTermChildren } from "@/hooks/useVocabularyTerm";
import type { VocabularyDefinition, VocabularyTerm } from "@/types/vocabulary";

const STORAGE_KEY = "vocabulary_parallel_mode";

function DefinitionPanel({
  definition,
  isJapanese,
}: {
  definition: VocabularyDefinition;
  isJapanese: boolean;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className={`text-sm font-medium ${isJapanese ? "text-jp" : ""}`}>
          {definition.language === "ja" ? "Japanese" : "English"}
        </span>
        {!definition.validated_against_jmdict && (
          <span title="Not validated against JMdict">
            <AlertTriangle className="size-4 text-amber-500" />
          </span>
        )}
      </div>
      <p className={`text-vocab-definition ${isJapanese ? "text-jp" : ""}`}>
        {definition.definition}
      </p>
      {definition.ipa && (
        <p className="font-mono text-sm text-zinc-600">{definition.ipa}</p>
      )}
      {definition.examples && definition.examples.length > 0 && (
        <div className="space-y-2">
          {definition.examples.map((example, idx) => (
            <div
              key={idx}
              className="bg-zinc-100 border-l-2 border-zinc-300 px-4 py-3 text-sm"
            >
              {example}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SingleLanguageView({
  term,
  definitions,
}: {
  term: VocabularyTerm;
  definitions: VocabularyDefinition[];
}) {
  const primaryLang = term.language;
  const filtered = definitions.filter((d) => d.language === primaryLang);

  if (filtered.length === 0) {
    return (
      <p className="text-sm text-text-secondary">No definition available for {primaryLang}</p>
    );
  }

  return (
    <div className="space-y-4">
      {filtered.map((def) => (
        <DefinitionPanel key={def.id} definition={def} isJapanese={primaryLang === "ja"} />
      ))}
    </div>
  );
}

function ParallelView({ definitions }: { definitions: VocabularyDefinition[] }) {
  const englishDefs = definitions.filter((d) => d.language === "en");
  const japaneseDefs = definitions.filter((d) => d.language === "ja");

  return (
    <div className="grid-cols-1 grid gap-6 md:grid-cols-2">
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-text-secondary">English</h3>
        {englishDefs.length === 0 ? (
          <p className="text-sm text-text-muted">No English definition</p>
        ) : (
          englishDefs.map((def) => (
            <DefinitionPanel key={def.id} definition={def} isJapanese={false} />
          ))
        )}
      </div>
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-text-secondary">Japanese</h3>
        {japaneseDefs.length === 0 ? (
          <p className="text-sm text-text-muted">No Japanese definition</p>
        ) : (
          japaneseDefs.map((def) => (
            <DefinitionPanel key={def.id} definition={def} isJapanese={true} />
          ))
        )}
      </div>
    </div>
  );
}

function TermDetailContent({ term }: { term: VocabularyTerm }) {
  const [isParallel, setIsParallel] = useState(() => {
    if (typeof window !== "undefined") {
      return sessionStorage.getItem(STORAGE_KEY) === "true";
    }
    return false;
  });
  const childrenQuery = useVocabularyTermChildren(term.id);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Tab" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const target = e.target as HTMLElement;
        if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;
        e.preventDefault();
        setIsParallel((prev) => {
          const next = !prev;
          sessionStorage.setItem(STORAGE_KEY, String(next));
          return next;
        });
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const toggleParallel = () => {
    setIsParallel((prev) => {
      const next = !prev;
      sessionStorage.setItem(STORAGE_KEY, String(next));
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/vocabulary">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="size-4" />
            </Button>
          </Link>
          <div className="flex flex-wrap items-center gap-2">
            {term.part_of_speech && (
              <span className="text-sm text-text-secondary">{term.part_of_speech}</span>
            )}
            {term.cefr_level && <Badge variant="outline">{term.cefr_level}</Badge>}
            {term.jlpt_level && <Badge variant="outline">{term.jlpt_level}</Badge>}
          </div>
        </div>
        <LanguageToggle isParallel={isParallel} onToggle={toggleParallel} />
      </div>

      {isParallel ? (
        <ParallelView definitions={term.definitions} />
      ) : (
        <SingleLanguageView term={term} definitions={term.definitions} />
      )}

      {childrenQuery.data && childrenQuery.data.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-text-secondary">Related Terms</h3>
          <div className="space-y-2">
            {childrenQuery.data.map((child) => (
              <Link
                key={child.id}
                href={`/vocabulary/${child.id}`}
                className="block rounded-md bg-zinc-100 border border-zinc-200 px-4 py-3 text-sm font-medium text-text-primary hover:bg-zinc-200 transition"
              >
                {child.term}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="h-9 w-9" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-16" />
            <Skeleton className="h-5 w-12" />
            <Skeleton className="h-5 w-12" />
          </div>
        </div>
        <Skeleton className="h-9 w-24" />
      </div>
      <div className="space-y-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-20 w-full" />
      </div>
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-center">
      <AlertTriangle className="size-10 text-destructive" />
      <div>
        <h3 className="text-lg font-semibold text-text-primary">Failed to load term</h3>
        <p className="mt-1 text-sm text-text-secondary">The vocabulary term could not be found</p>
      </div>
      <Button variant="outline" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}

function NotFoundState() {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-center">
      <AlertTriangle className="size-10 text-zinc-400" />
      <div>
        <h3 className="text-lg font-semibold text-text-primary">Term not found</h3>
        <p className="mt-1 text-sm text-text-secondary">
          This vocabulary term does not exist or has been removed
        </p>
      </div>
      <Link href="/vocabulary">
        <Button variant="outline">Back to vocabulary</Button>
      </Link>
    </div>
  );
}

export default function VocabularyTermPage() {
  const params = useParams();
  const termId = Number(params.termId);

  const termQuery = useVocabularyTerm(termId);

  if (termQuery.isError) {
    return <ErrorState onRetry={() => termQuery.refetch()} />;
  }

  if (termQuery.isLoading) {
    return (
      <section className="mx-auto flex w-full max-w-[720px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-0">
        <LoadingSkeleton />
      </section>
    );
  }

  if (!termQuery.data) {
    return (
      <section className="mx-auto flex w-full max-w-[720px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-0">
        <NotFoundState />
      </section>
    );
  }

  const term = termQuery.data;

  return (
    <section className="mx-auto flex w-full max-w-[720px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-0">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-zinc-950">{term.term}</h1>
        <p className="text-sm text-text-secondary">({term.language})</p>
      </div>
      <TermDetailContent term={term} />
    </section>
  );
}
