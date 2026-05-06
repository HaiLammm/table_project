"use client";

import { useEffect, useEffectEvent, useMemo, useState } from "react";
import { FileText, FolderOpen, Search } from "lucide-react";
import { useRouter } from "next/navigation";

import {
  Command,
  CommandDialog,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import { useVocabularySearch } from "@/hooks/useVocabularySearch";
import type { VocabularyTerm } from "@/types/vocabulary";

const RECENT_SEARCHES_KEY = "command-palette-recent";
const MAX_RECENT_SEARCHES = 5;

type CommandPaletteProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

type RecentSearchKind = "page" | "word" | "collection";

type RecentSearch = {
  id: string;
  href: string;
  kind: RecentSearchKind;
  title: string;
  subtitle?: string;
};

type PageResult = {
  id: string;
  href: string;
  title: string;
  keywords: string[];
  shortcut?: string;
};

const pageResults: PageResult[] = [
  { id: "dashboard", href: "/dashboard", title: "Dashboard", keywords: ["progress", "stats"] },
  { id: "vocabulary", href: "/vocabulary", title: "Vocabulary", keywords: ["words", "terms", "search"] },
  { id: "collections", href: "/collections", title: "Collections", keywords: ["folders", "study lists"] },
  { id: "review", href: "/review", title: "Review", keywords: ["queue", "practice"] },
  { id: "diagnostics", href: "/diagnostics", title: "Diagnostics", keywords: ["insights", "analytics"] },
  { id: "settings", href: "/settings", title: "Settings", keywords: ["preferences", "profile"], shortcut: "," },
];

function isTypingTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  const tagName = target.tagName.toLowerCase();
  return target.isContentEditable || tagName === "input" || tagName === "textarea" || tagName === "select";
}

function readRecentSearches() {
  if (typeof window === "undefined") {
    return [] as RecentSearch[];
  }

  try {
    const stored = window.localStorage.getItem(RECENT_SEARCHES_KEY);

    if (stored === null) {
      return [];
    }

    const parsed = JSON.parse(stored) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .filter((item): item is RecentSearch => {
        return typeof item === "object" && item !== null && "id" in item && "href" in item && "kind" in item && "title" in item;
      })
      .slice(0, MAX_RECENT_SEARCHES);
  } catch {
    return [];
  }
}

function writeRecentSearches(searches: RecentSearch[]) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(searches.slice(0, MAX_RECENT_SEARCHES)));
}

function buildRecentWord(term: VocabularyTerm): RecentSearch {
  const firstDefinition = term.definitions[0]?.definition;
  const subtitle = [term.language.toUpperCase(), firstDefinition].filter(Boolean).join(" • ");

  return {
    id: String(term.id),
    href: `/vocabulary/${term.id}`,
    kind: "word",
    title: term.term,
    subtitle: subtitle || undefined,
  };
}

function buildRecentPage(page: PageResult): RecentSearch {
  return {
    id: page.id,
    href: page.href,
    kind: "page",
    title: page.title,
    subtitle: page.href,
  };
}

function updateRecentSearches(search: RecentSearch, current: RecentSearch[]) {
  const next = [search, ...current.filter((item) => !(item.kind === search.kind && item.id === search.id && item.href === search.href))].slice(
    0,
    MAX_RECENT_SEARCHES,
  );

  writeRecentSearches(next);
  return next;
}

function EmptyRecentState() {
  return (
    <div className="px-6 py-12 text-center text-sm text-zinc-400">
      Start typing to search pages and vocabulary. Your last 5 selections will appear here.
    </div>
  );
}

function EmptyGroupState({ message }: { message: string }) {
  return (
    <CommandItem disabled value={message} className="text-zinc-500">
      <span>{message}</span>
    </CommandItem>
  );
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>(() => readRecentSearches());

  const trimmedQuery = open ? query.trim() : "";
  const vocabularySearch = useVocabularySearch(trimmedQuery);

  const filteredPages = useMemo(() => {
    if (trimmedQuery.length === 0) {
      return [] as PageResult[];
    }

    const normalizedQuery = trimmedQuery.toLowerCase();

    return pageResults.filter((page) => {
      const haystack = [page.title, page.href, ...page.keywords].join(" ").toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [trimmedQuery]);

  const wordResults = trimmedQuery.length >= 2 ? (vocabularySearch.data?.items ?? []) : [];
  const loadingWords = trimmedQuery.length >= 2 && vocabularySearch.isLoading;

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      setQuery("");
    }

    onOpenChange(nextOpen);
  };

  const openPalette = useEffectEvent(() => {
    onOpenChange(true);
  });

  const closePalette = useEffectEvent(() => {
    handleOpenChange(false);
  });

  useEffect(() => {
    if (open) {
      const timeoutId = window.setTimeout(() => {
        setRecentSearches(readRecentSearches());
      }, 0);

      return () => {
        window.clearTimeout(timeoutId);
      };
    }
  }, [open]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const pressedShortcut = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
      if (pressedShortcut) {
        if (isTypingTarget(event.target)) {
          return;
        }

        event.preventDefault();
        openPalette();
        return;
      }

      if (event.key === "Escape" && open) {
        closePalette();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const handleSelect = (search: RecentSearch) => {
    setRecentSearches((current) => updateRecentSearches(search, current));
    handleOpenChange(false);
    router.push(search.href);
  };

  const showSearchResults = trimmedQuery.length > 0;

  return (
    <CommandDialog
      open={open}
      onOpenChange={handleOpenChange}
      className="top-0 max-w-screen rounded-none border-x-0 border-t-0 sm:top-[10vh] sm:max-w-2xl sm:rounded-2xl sm:border"
      title="Search everything"
      description="Quickly search vocabulary, collections, and app pages."
    >
      <Command shouldFilter={false} loop>
        <CommandInput
          autoFocus
          value={query}
          onValueChange={setQuery}
          placeholder="Search vocabulary, collections, or pages..."
        />

        {showSearchResults ? (
          <CommandList>
            <CommandGroup heading="Pages">
              {filteredPages.length > 0 ? (
                filteredPages.map((page) => (
                  <CommandItem
                    key={page.id}
                    value={`${page.title} ${page.href} ${page.keywords.join(" ")}`}
                    onSelect={() => handleSelect(buildRecentPage(page))}
                  >
                    <FileText className="size-4 text-zinc-500" />
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium text-zinc-100">{page.title}</div>
                      <div className="truncate text-xs text-zinc-500">{page.href}</div>
                    </div>
                    {page.shortcut ? <CommandShortcut>{page.shortcut}</CommandShortcut> : null}
                  </CommandItem>
                ))
              ) : (
                <EmptyGroupState message="No matching pages" />
              )}
            </CommandGroup>

            <CommandSeparator />

            <CommandGroup heading="Collections">
              <EmptyGroupState message="Collection search is coming soon" />
            </CommandGroup>

            <CommandSeparator />

            <CommandGroup heading="Words">
              {loadingWords ? (
                <EmptyGroupState message="Searching vocabulary..." />
              ) : wordResults.length > 0 ? (
                wordResults.map((term) => {
                  const firstDefinition = term.definitions[0]?.definition;

                  return (
                    <CommandItem
                      key={term.id}
                      value={`${term.term} ${term.language} ${firstDefinition ?? ""}`}
                      onSelect={() => handleSelect(buildRecentWord(term))}
                    >
                      <Search className="size-4 text-zinc-500" />
                      <div className="min-w-0 flex-1">
                        <div className="truncate font-medium text-zinc-100">{term.term}</div>
                        <div className="truncate text-xs text-zinc-500">
                          {[term.language.toUpperCase(), firstDefinition].filter(Boolean).join(" • ") || "Vocabulary result"}
                        </div>
                      </div>
                    </CommandItem>
                  );
                })
              ) : trimmedQuery.length < 2 ? (
                <EmptyGroupState message="Type at least 2 characters to search words" />
              ) : vocabularySearch.isError ? (
                <EmptyGroupState message="Unable to search vocabulary right now" />
              ) : (
                <EmptyGroupState message="No matching words" />
              )}
            </CommandGroup>
          </CommandList>
        ) : (
          <CommandList>
            {recentSearches.length > 0 ? (
              <CommandGroup heading="Recent Searches">
                {recentSearches.map((item) => (
                  <CommandItem key={`${item.kind}-${item.id}`} value={`${item.title} ${item.subtitle ?? ""}`} onSelect={() => handleSelect(item)}>
                    {item.kind === "collection" ? (
                      <FolderOpen className="size-4 text-zinc-500" />
                    ) : item.kind === "page" ? (
                      <FileText className="size-4 text-zinc-500" />
                    ) : (
                      <Search className="size-4 text-zinc-500" />
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium text-zinc-100">{item.title}</div>
                      {item.subtitle ? <div className="truncate text-xs text-zinc-500">{item.subtitle}</div> : null}
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            ) : (
              <EmptyRecentState />
            )}
          </CommandList>
        )}
      </Command>
    </CommandDialog>
  );
}
