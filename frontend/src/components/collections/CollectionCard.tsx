"use client";

import { type KeyboardEvent, useEffect, useRef, useState } from "react";
import { MoreHorizontal, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

export interface CollectionCardProps {
  icon: string;
  name: string;
  termCount: number;
  masteryPercent: number;
  variant?: "default" | "create";
  onClick: () => void;
  onRename?: (newName: string) => void | Promise<void>;
  onDelete?: () => void;
}

export function CollectionCard({
  icon,
  name,
  termCount,
  masteryPercent,
  variant = "default",
  onClick,
  onRename,
  onDelete,
}: CollectionCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draftName, setDraftName] = useState(name);
  const [isSubmittingRename, setIsSubmittingRename] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isEditing) {
      return;
    }

    inputRef.current?.focus();
    inputRef.current?.select();
  }, [isEditing]);

  if (variant === "create") {
    return (
      <button
        type="button"
        onClick={onClick}
        className="flex min-h-[184px] w-full flex-col items-center justify-center gap-3 rounded-[10px] border border-dashed border-zinc-300 bg-zinc-50 p-5 text-center transition-colors hover:border-zinc-400 hover:bg-zinc-100"
      >
        <div className="flex size-12 items-center justify-center rounded-full border border-dashed border-zinc-400 bg-white text-zinc-700">
          <Plus className="size-5" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-semibold text-text-primary">+ New Collection</p>
          <p className="text-xs text-text-secondary">Start grouping terms by topic or project</p>
        </div>
      </button>
    );
  }

  const clampedMasteryPercent = Math.max(0, Math.min(100, masteryPercent));

  async function submitRename() {
    const trimmedName = draftName.trim();
    if (!trimmedName || trimmedName === name || onRename === undefined) {
      setDraftName(name);
      setIsEditing(false);
      return;
    }

    setIsSubmittingRename(true);
    try {
      await onRename(trimmedName);
      setIsEditing(false);
    } catch {
      inputRef.current?.focus();
      inputRef.current?.select();
    } finally {
      setIsSubmittingRename(false);
    }
  }

  function handleCardKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (isEditing) {
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onClick();
    }
  }

  function handleRenameKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      void submitRename();
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      setDraftName(name);
      setIsEditing(false);
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => {
        if (!isEditing) {
          onClick();
        }
      }}
      onKeyDown={handleCardKeyDown}
      className="min-h-[184px] rounded-[10px] border border-zinc-200 bg-zinc-100 p-5 text-left transition-colors hover:bg-zinc-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 text-2xl leading-none" aria-hidden="true">
              {icon}
            </span>
            <div className="min-w-0 flex-1 space-y-1">
              {isEditing ? (
                <input
                  ref={inputRef}
                  value={draftName}
                  disabled={isSubmittingRename}
                  onChange={(event) => setDraftName(event.target.value)}
                  onKeyDown={handleRenameKeyDown}
                  onBlur={() => {
                    if (!isSubmittingRename) {
                      setDraftName(name);
                      setIsEditing(false);
                    }
                  }}
                  className="w-full rounded-md border border-zinc-300 bg-white px-2 py-1 text-base font-semibold text-text-primary outline-none ring-0 focus-visible:border-zinc-400"
                  aria-label="Collection name"
                />
              ) : (
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    if (onRename) {
                      setDraftName(name);
                      setIsEditing(true);
                    }
                  }}
                  className={cn(
                    "truncate text-left text-base font-semibold text-text-primary",
                    onRename ? "cursor-text" : "cursor-default",
                  )}
                >
                  {name}
                </button>
              )}
              <p className="text-sm text-text-secondary">
                {termCount} term{termCount === 1 ? "" : "s"}
              </p>
            </div>
          </div>
        </div>

        {onRename || onDelete ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label={`Open actions for ${name}`}
                onClick={(event) => event.stopPropagation()}
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" onClick={(event) => event.stopPropagation()}>
              {onRename ? (
                <DropdownMenuItem
                  onSelect={(event) => {
                    event.preventDefault();
                    setDraftName(name);
                    setIsEditing(true);
                  }}
                >
                  Rename
                </DropdownMenuItem>
              ) : null}
              {onRename && onDelete ? <DropdownMenuSeparator /> : null}
              {onDelete ? (
                <DropdownMenuItem
                  className="text-red-300 focus:bg-red-950 focus:text-red-100"
                  onSelect={(event) => {
                    event.preventDefault();
                    onDelete();
                  }}
                >
                  Delete
                </DropdownMenuItem>
              ) : null}
            </DropdownMenuContent>
          </DropdownMenu>
        ) : null}
      </div>

      <div className="mt-8 space-y-2">
        <div className="flex items-center justify-between text-sm text-text-secondary">
          <span>Mastery</span>
          <span className="font-medium text-text-primary">{clampedMasteryPercent}%</span>
        </div>
        <div className="h-2 rounded-full bg-zinc-200">
          <div
            className="h-full rounded-full bg-zinc-600 transition-[width]"
            style={{ width: `${clampedMasteryPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}
