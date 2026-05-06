"use client";

import { Search, ChevronLeft, ChevronRight, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { AddTermForm } from "@/components/vocabulary/AddTermForm";
import { useVocabularyList } from "@/hooks/useVocabularyList";
import { useVocabularySearch } from "@/hooks/useVocabularySearch";
import type { VocabularyTerm } from "@/types/vocabulary";

const CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const JLPT_LEVELS = ["N5", "N4", "N3", "N2", "N1"];

interface TermCardProps {
  term: VocabularyTerm;
}

function TermCard({ term }: TermCardProps) {
  const firstDefinition = term.definitions[0];

  return (
    <Link href={`/vocabulary/${term.id}`} className="block">
      <Card className="bg-zinc-100 border border-zinc-200 rounded-[10px] p-5">
        <CardContent className="p-0">
          <div className="flex flex-col gap-2">
            <div className="flex items-start justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-base font-semibold text-text-primary">{term.term}</span>
                <span className="text-sm text-text-secondary">({term.language})</span>
                {term.part_of_speech && (
                  <span className="text-xs text-text-secondary">{term.part_of_speech}</span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-1">
                {term.cefr_level && (
                  <Badge variant="outline">{term.cefr_level}</Badge>
                )}
                {term.jlpt_level && (
                  <Badge variant="outline">{term.jlpt_level}</Badge>
                )}
              </div>
            </div>
            {firstDefinition && (
              <p className="text-sm text-text-secondary line-clamp-2">
                {firstDefinition.definition}
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function TermCardSkeleton() {
  return (
    <Card className="bg-zinc-100 border border-zinc-200 rounded-[10px] p-5">
      <CardContent className="p-0">
        <div className="flex flex-col gap-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-4 w-8" />
            </div>
            <div className="flex flex-wrap items-center gap-1">
              <Skeleton className="h-5 w-10" />
              <Skeleton className="h-5 w-10" />
            </div>
          </div>
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState({ query }: { query: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-center">
      <Search className="size-10 text-zinc-400" />
      <div>
        <h3 className="text-lg font-semibold text-text-primary">No results found</h3>
        <p className="mt-1 text-sm text-text-secondary">
          {query ? `No vocabulary terms match "${query}"` : "Try adjusting your filters or search terms"}
        </p>
      </div>
    </div>
  );
}

interface SearchResultsProps {
  query: string;
  onClear: () => void;
}

function SearchResults({ query, onClear }: SearchResultsProps) {
  const searchQuery = useVocabularySearch(query);

  if (searchQuery.isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <TermCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (searchQuery.isError) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-center">
        <p className="text-sm text-destructive">Failed to load search results</p>
        <Button variant="outline" onClick={() => searchQuery.refetch()}>
          Try again
        </Button>
      </div>
    );
  }

  const items = searchQuery.data?.items ?? [];

  if (items.length === 0) {
    return <EmptyState query={query} />;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-text-secondary">
          {items.length} result{items.length !== 1 ? "s" : ""} for &quot;{query}&quot;
        </p>
        <Button variant="ghost" size="sm" onClick={onClear}>
          Clear
        </Button>
      </div>
      {items.map((term) => (
        <TermCard key={term.id} term={term} />
      ))}
    </div>
  );
}

interface VocabularyBrowserProps {
  page: number;
  setPage: (page: number | ((prev: number) => number)) => void;
  cefrLevel: string | undefined;
  jlptLevel: string | undefined;
  parentId?: number | undefined;
}

function VocabularyBrowser({
  page,
  setPage,
  cefrLevel,
  jlptLevel,
}: VocabularyBrowserProps) {
  const listQuery = useVocabularyList({
    page,
    page_size: 20,
    cefr_level: cefrLevel,
    jlpt_level: jlptLevel,
    parent_id: undefined,
  });

  if (listQuery.isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <TermCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (listQuery.isError) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-center">
        <p className="text-sm text-destructive">Failed to load vocabulary</p>
        <Button variant="outline" onClick={() => listQuery.refetch()}>
          Try again
        </Button>
      </div>
    );
  }

  const items = listQuery.data?.items ?? [];
  const total = listQuery.data?.total ?? 0;
  const pageSize = listQuery.data?.page_size ?? 20;
  const hasNext = listQuery.data?.has_next ?? false;
  const totalPages = Math.ceil(total / pageSize);

  if (items.length === 0) {
    return <EmptyState query="" />;
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {items.map((term) => (
          <TermCard key={term.id} term={term} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <span className="text-sm text-text-secondary">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={!hasNext}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

export default function VocabularyPage() {
  const [page, setPage] = useState(1);
  const [cefrLevel, setCefrLevel] = useState<string | undefined>(undefined);
  const [jlptLevel, setJlptLevel] = useState<string | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const query = formData.get("query") as string;
    if (query.trim()) {
      setSearchQuery(query.trim());
      setIsSearching(true);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setIsSearching(false);
  };

  const handleCefrChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCefrLevel(e.target.value || undefined);
    setPage(1);
    setIsSearching(false);
  };

  const handleJlptChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setJlptLevel(e.target.value || undefined);
    setPage(1);
    setIsSearching(false);
  };

  return (
    <section className="mx-auto flex w-full max-w-[720px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-0">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <h1 className="text-display text-text-primary">Vocabulary</h1>
          <p className="text-body text-text-secondary">
            Browse and search your vocabulary corpus
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2"
        >
          <Plus className="size-4" />
          Add Term
        </Button>
        <Link href="/vocabulary/request">
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            Request Terms
          </Button>
        </Link>
        <Link href="/vocabulary/import">
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            Import CSV
          </Button>
        </Link>
      </div>

      {showAddForm && (
        <Card className="bg-zinc-50 border border-zinc-200 rounded-[10px] p-5">
          <CardContent className="p-0">
            <AddTermForm onTermCreated={() => {
              setShowAddForm(false);
            }} />
          </CardContent>
        </Card>
      )}

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-zinc-400" />
          <input
            type="text"
            name="query"
            placeholder="Search vocabulary..."
            className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 pl-10 text-sm w-full outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10"
          />
        </div>
        <Button type="submit">Search</Button>
      </form>

      <div className="flex flex-wrap gap-3">
        <Select
          value={cefrLevel ?? ""}
          onChange={handleCefrChange}
          className="w-28"
        >
          <option value="">CEFR</option>
          {CEFR_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </Select>

        <Select
          value={jlptLevel ?? ""}
          onChange={handleJlptChange}
          className="w-28"
        >
          <option value="">JLPT</option>
          {JLPT_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </Select>
      </div>

      {isSearching ? (
        <SearchResults query={searchQuery} onClear={handleClearSearch} />
      ) : (
        <VocabularyBrowser
          page={page}
          setPage={setPage}
          cefrLevel={cefrLevel}
          jlptLevel={jlptLevel}
          parentId={undefined}
        />
      )}
    </section>
  );
}
