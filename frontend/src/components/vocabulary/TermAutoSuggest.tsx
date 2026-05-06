"use client";

import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { useVocabularySearch } from "@/hooks/useVocabularySearch";
import type { VocabularyTerm } from "@/types/vocabulary";

interface TermAutoSuggestProps {
  value: string;
  onChange: (value: string) => void;
  onSelect: (term: VocabularyTerm) => void;
  onCreateNew: () => void;
  placeholder?: string;
}

export function TermAutoSuggest({
  value,
  onChange,
  onSelect,
  onCreateNew,
  placeholder = "Type to search...",
}: TermAutoSuggestProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [showCreateOption, setShowCreateOption] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const searchQuery = useVocabularySearch(value);

  const suggestions = searchQuery.data?.items ?? [];
  const hasResults = suggestions.length > 0;

  useEffect(() => {
    const shouldShowCreate = value.length >= 2 && !hasResults && !searchQuery.isLoading;
    setShowCreateOption(shouldShowCreate);
  }, [value, hasResults, searchQuery.isLoading]);

  useEffect(() => {
    if (isOpen) {
      setActiveIndex(-1);
    }
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    const totalItems = suggestions.length + (showCreateOption ? 1 : 0);

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((prev) => (prev < totalItems - 1 ? prev + 1 : prev));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case "Enter":
        e.preventDefault();
        if (activeIndex === suggestions.length && showCreateOption) {
          onCreateNew();
        } else if (activeIndex >= 0 && activeIndex < suggestions.length) {
          onSelect(suggestions[activeIndex]);
          setIsOpen(false);
          onChange("");
        }
        break;
      case "Escape":
        setIsOpen(false);
        setActiveIndex(-1);
        break;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    setIsOpen(newValue.length >= 2);
  };

  const handleSuggestionClick = (term: VocabularyTerm) => {
    onSelect(term);
    setIsOpen(false);
    onChange("");
  };

  const handleCreateClick = () => {
    onCreateNew();
    setIsOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => value.length >= 2 && setIsOpen(true)}
        placeholder={placeholder}
        className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm w-full outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10"
        aria-autocomplete="list"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      />

      {isOpen && (hasResults || showCreateOption) && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-zinc-200 rounded-[10px] shadow-lg overflow-hidden">
          {hasResults && (
            <ul role="listbox" className="max-h-60 overflow-y-auto">
              {suggestions.map((term, index) => (
                <li
                  key={term.id}
                  role="option"
                  aria-selected={index === activeIndex}
                  onClick={() => handleSuggestionClick(term)}
                  className={`px-4 py-2.5 cursor-pointer transition flex items-center justify-between gap-2 ${
                    index === activeIndex ? "bg-zinc-100" : "hover:bg-zinc-50"
                  }`}
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-text-primary">{term.term}</span>
                    {term.language === "jp" && term.part_of_speech && (
                      <span className="text-xs text-text-secondary">({term.part_of_speech})</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    {term.cefr_level && <Badge variant="outline">{term.cefr_level}</Badge>}
                    {term.jlpt_level && <Badge variant="outline">{term.jlpt_level}</Badge>}
                  </div>
                </li>
              ))}
            </ul>
          )}
          {showCreateOption && (
            <div
              onClick={handleCreateClick}
              className={`px-4 py-2.5 cursor-pointer border-t border-zinc-100 transition ${
                activeIndex === suggestions.length ? "bg-zinc-100" : "hover:bg-zinc-50"
              }`}
            >
              <span className="text-sm text-zinc-600">Add &quot;{value}&quot; as new term</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}