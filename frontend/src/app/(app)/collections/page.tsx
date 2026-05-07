"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { ArrowLeft, ChevronLeft, ChevronRight, FolderOpen, X } from "lucide-react";

import { AddWordsDialog } from "@/components/collections/AddWordsDialog";
import { CollectionCard } from "@/components/collections";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import {
  useAddTermToCollection,
  useCollectionTerms,
  useCollections,
  useCreateCollection,
  useDeleteCollection,
  useRemoveTermFromCollection,
  useUpdateCollection,
} from "@/hooks/useCollections";
import { ApiClientError } from "@/lib/api-client";
import type { Collection, CollectionTerm } from "@/types/collection";

const ICON_OPTIONS = [
  "📚",
  "🌍",
  "💼",
  "💻",
  "🧪",
  "📝",
  "🎯",
  "🧠",
  "🏢",
  "✈️",
  "💬",
  "📈",
  "🔬",
  "🎓",
  "🧳",
  "📦",
  "⚙️",
  "🎨",
  "🏷️",
  "🔥",
];

function getErrorMessage(error: unknown) {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong";
}

function getMasteryBadgeClassName(status: CollectionTerm["mastery_status"]) {
  if (status === "mastered") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }

  if (status === "learning") {
    return "border-amber-200 bg-amber-50 text-amber-800";
  }

  return "border-zinc-200 bg-zinc-100 text-zinc-700";
}

function CollectionCardSkeleton() {
  return (
    <div className="min-h-[184px] rounded-[10px] border border-zinc-200 bg-zinc-100 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-1 items-start gap-3">
          <Skeleton className="size-10 rounded-full" />
          <div className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-16" />
          </div>
        </div>
        <Skeleton className="size-10 rounded-lg" />
      </div>
      <div className="mt-8 space-y-2">
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-10" />
        </div>
        <Skeleton className="h-2 w-full rounded-full" />
      </div>
    </div>
  );
}

function TermRowSkeleton() {
  return (
    <div className="rounded-[12px] border border-zinc-200 bg-white p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-4 w-40" />
        </div>
        <Skeleton className="size-9 rounded-full" />
      </div>
    </div>
  );
}

interface EmptyStateProps {
  onCreate: () => void;
}

function EmptyState({ onCreate }: EmptyStateProps) {
  return (
    <section className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <div className="flex size-16 items-center justify-center rounded-full border border-zinc-200 bg-zinc-100 text-zinc-500">
        <FolderOpen className="size-7" />
      </div>
      <div className="space-y-2">
        <h1 className="text-display text-text-primary">No collections yet</h1>
        <p className="max-w-md text-body text-text-secondary">
          Create your first collection to organize vocabulary by topic, exam, or project.
        </p>
      </div>
      <Button type="button" variant="outline" onClick={onCreate}>
        + New Collection
      </Button>
    </section>
  );
}

interface CollectionDetailProps {
  collection: Collection;
  terms: CollectionTerm[];
  page: number;
  totalPages: number;
  hasNext: boolean;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  onBack: () => void;
  onAddWords: () => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
  onRemoveTerm: (term: CollectionTerm) => void;
  isRemovingTerm: boolean;
}

function CollectionDetail({
  collection,
  terms,
  page,
  totalPages,
  hasNext,
  isLoading,
  isError,
  onRetry,
  onBack,
  onAddWords,
  onPreviousPage,
  onNextPage,
  onRemoveTerm,
  isRemovingTerm,
}: CollectionDetailProps) {
  return (
    <section className="space-y-6">
      <div className="space-y-4 rounded-[16px] border border-zinc-200 bg-zinc-100 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-3">
            <Button type="button" variant="ghost" size="sm" onClick={onBack} className="gap-1.5">
              <ArrowLeft className="size-4" />
              Back to collections
            </Button>

            <div className="flex items-start gap-3">
              <div className="flex size-12 items-center justify-center rounded-full border border-zinc-200 bg-white text-2xl">
                <span aria-hidden="true">{collection.icon}</span>
              </div>
              <div className="space-y-1">
                <h1 className="text-display text-text-primary">{collection.name}</h1>
                <div className="flex flex-wrap items-center gap-2 text-sm text-text-secondary">
                  <span>{collection.term_count} terms</span>
                  <span>•</span>
                  <span>{collection.mastery_percent}% mastered</span>
                </div>
              </div>
            </div>
          </div>

          <Button type="button" onClick={onAddWords} className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800">
            Add Words
          </Button>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm text-text-secondary">
            <span>Mastery</span>
            <span className="font-medium text-text-primary">{collection.mastery_percent}%</span>
          </div>
          <div className="h-2 rounded-full bg-zinc-200">
            <div
              className="h-full rounded-full bg-zinc-600 transition-[width]"
              style={{ width: `${collection.mastery_percent}%` }}
            />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-text-primary">Terms</h2>
            <p className="text-sm text-text-secondary">
              Review what belongs to this collection and remove anything you no longer need.
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, index) => (
              <TermRowSkeleton key={index} />
            ))}
          </div>
        ) : null}

        {isError ? (
          <div className="flex min-h-[30vh] flex-col items-center justify-center gap-3 rounded-[14px] border border-zinc-200 bg-zinc-50 px-6 py-10 text-center">
            <p className="text-sm text-text-secondary">Failed to load collection terms.</p>
            <Button type="button" variant="outline" onClick={onRetry}>
              Try again
            </Button>
          </div>
        ) : null}

        {!isLoading && !isError && terms.length === 0 ? (
          <div className="flex min-h-[30vh] flex-col items-center justify-center gap-3 rounded-[14px] border border-dashed border-zinc-300 bg-zinc-50 px-6 py-10 text-center">
            <p className="text-lg font-semibold text-text-primary">No terms yet</p>
            <p className="max-w-md text-sm text-text-secondary">
              Add words manually, browse the corpus, or import a CSV file to start building this study set.
            </p>
            <Button type="button" onClick={onAddWords} className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800">
              Add Words
            </Button>
          </div>
        ) : null}

        {!isLoading && !isError && terms.length > 0 ? (
          <div className="space-y-3">
            {terms.map((term) => (
              <div
                key={term.term_id}
                className="rounded-[12px] border border-zinc-200 bg-white px-4 py-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        href={`/vocabulary/${term.term_id}`}
                        className="text-base font-semibold text-text-primary transition hover:text-zinc-700"
                      >
                        {term.term}
                      </Link>
                      <span className="text-xs uppercase tracking-wide text-zinc-500">{term.language}</span>
                      {term.part_of_speech ? (
                        <span className="text-sm text-text-secondary">{term.part_of_speech}</span>
                      ) : null}
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline" className={getMasteryBadgeClassName(term.mastery_status)}>
                        {term.mastery_status}
                      </Badge>
                      {term.cefr_level ? <Badge variant="outline">{term.cefr_level}</Badge> : null}
                      {term.jlpt_level ? <Badge variant="outline">{term.jlpt_level}</Badge> : null}
                    </div>
                  </div>

                  <button
                    type="button"
                    aria-label={`Remove ${term.term} from collection`}
                    onClick={() => onRemoveTerm(term)}
                    disabled={isRemovingTerm}
                    className="flex size-9 items-center justify-center rounded-full border border-zinc-200 bg-zinc-50 text-zinc-500 transition hover:border-zinc-300 hover:bg-zinc-100 hover:text-zinc-900 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <X className="size-4" />
                  </button>
                </div>
              </div>
            ))}

            {totalPages > 1 ? (
              <div className="flex items-center justify-center gap-2 pt-2">
                <Button type="button" variant="outline" size="sm" onClick={onPreviousPage} disabled={page === 1}>
                  <ChevronLeft className="size-4" />
                </Button>
                <span className="text-sm text-text-secondary">
                  Page {page} of {totalPages}
                </span>
                <Button type="button" variant="outline" size="sm" onClick={onNextPage} disabled={!hasNext}>
                  <ChevronRight className="size-4" />
                </Button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}

export default function CollectionsPage() {
  const toast = useToast();
  const collectionsQuery = useCollections();
  const createCollection = useCreateCollection();
  const updateCollection = useUpdateCollection();
  const deleteCollection = useDeleteCollection();

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isAddWordsDialogOpen, setIsAddWordsDialogOpen] = useState(false);
  const [collectionName, setCollectionName] = useState("");
  const [collectionIcon, setCollectionIcon] = useState(ICON_OPTIONS[0]);
  const [collectionToDelete, setCollectionToDelete] = useState<Collection | null>(null);
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null);
  const [termsPage, setTermsPage] = useState(1);

  const collections = collectionsQuery.data?.items ?? [];
  const selectedCollection = collections.find((collection) => collection.id === selectedCollectionId) ?? null;

  const termsQuery = useCollectionTerms(selectedCollectionId, termsPage);
  const removeTerm = useRemoveTermFromCollection(selectedCollectionId ?? 0);
  const addTermToCollection = useAddTermToCollection(selectedCollectionId ?? 0);

  async function handleCreateCollection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await createCollection.mutateAsync({
        name: collectionName.trim(),
        icon: collectionIcon,
      });
      setCollectionName("");
      setCollectionIcon(ICON_OPTIONS[0]);
      setIsCreateDialogOpen(false);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  }

  async function handleRenameCollection(collectionId: number, name: string) {
    try {
      await updateCollection.mutateAsync({
        collectionId,
        data: { name },
      });
    } catch (error) {
      toast.error(getErrorMessage(error));
      throw error;
    }
  }

  async function handleDeleteCollection() {
    if (collectionToDelete === null) {
      return;
    }

    try {
      await deleteCollection.mutateAsync(collectionToDelete.id);
      if (selectedCollectionId === collectionToDelete.id) {
        setSelectedCollectionId(null);
        setTermsPage(1);
        setIsAddWordsDialogOpen(false);
      }
      setCollectionToDelete(null);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  }

  async function handleRemoveTerm(term: CollectionTerm) {
    if (selectedCollectionId === null) {
      return;
    }

    try {
      await removeTerm.mutateAsync(term.term_id);
      toast.showUndoToast({
        message: "Term removed from collection",
        action: {
          label: "Undo",
          onClick: () => {
            void addTermToCollection.mutateAsync({ term_id: term.term_id }).catch((error) => {
              toast.error(getErrorMessage(error));
            });
          },
        },
      });
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  }

  if (collectionsQuery.isLoading && selectedCollectionId === null) {
    return (
      <section className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-display text-text-primary">Collections</h1>
          <p className="text-body text-text-secondary">
            Organize vocabulary by topic, exam, or project.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[...Array(4)].map((_, index) => (
            <CollectionCardSkeleton key={index} />
          ))}
        </div>
      </section>
    );
  }

  if (collectionsQuery.isError) {
    return (
      <section className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
        <div className="space-y-2">
          <h1 className="text-display text-text-primary">Collections</h1>
          <p className="text-body text-text-secondary">Failed to load collections.</p>
        </div>
        <Button type="button" variant="outline" onClick={() => collectionsQuery.refetch()}>
          Try again
        </Button>
      </section>
    );
  }

  const totalPages = Math.max(1, Math.ceil((termsQuery.data?.total ?? 0) / (termsQuery.data?.page_size ?? 20)));

  return (
    <>
      {selectedCollection ? (
        <CollectionDetail
          collection={selectedCollection}
          terms={termsQuery.data?.items ?? []}
          page={termsPage}
          totalPages={totalPages}
          hasNext={termsQuery.data?.has_next ?? false}
          isLoading={termsQuery.isLoading}
          isError={termsQuery.isError}
          onRetry={() => termsQuery.refetch()}
          onBack={() => {
            setSelectedCollectionId(null);
            setTermsPage(1);
            setIsAddWordsDialogOpen(false);
          }}
          onAddWords={() => setIsAddWordsDialogOpen(true)}
          onPreviousPage={() => setTermsPage((current) => Math.max(1, current - 1))}
          onNextPage={() => setTermsPage((current) => current + 1)}
          onRemoveTerm={(term) => void handleRemoveTerm(term)}
          isRemovingTerm={removeTerm.isPending}
        />
      ) : collections.length === 0 ? (
        <EmptyState onCreate={() => setIsCreateDialogOpen(true)} />
      ) : (
        <section className="space-y-6">
          <div className="space-y-2">
            <h1 className="text-display text-text-primary">Collections</h1>
            <p className="text-body text-text-secondary">
              Organize vocabulary by topic, exam, or project.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {collections.map((collection) => (
              <CollectionCard
                key={collection.id}
                icon={collection.icon}
                name={collection.name}
                termCount={collection.term_count}
                masteryPercent={collection.mastery_percent}
                onClick={() => {
                  setSelectedCollectionId(collection.id);
                  setTermsPage(1);
                  setIsAddWordsDialogOpen(false);
                }}
                onRename={(nextName) => handleRenameCollection(collection.id, nextName)}
                onDelete={() => setCollectionToDelete(collection)}
              />
            ))}
            <CollectionCard
              icon="+"
              name="New Collection"
              termCount={0}
              masteryPercent={0}
              variant="create"
              onClick={() => setIsCreateDialogOpen(true)}
            />
          </div>
        </section>
      )}

      <Dialog
        open={isCreateDialogOpen}
        onOpenChange={(open) => {
          setIsCreateDialogOpen(open);
          if (!open) {
            setCollectionName("");
            setCollectionIcon(ICON_OPTIONS[0]);
          }
        }}
      >
        <DialogContent aria-describedby="create-collection-description">
          <DialogHeader>
            <DialogTitle>Create Collection</DialogTitle>
            <DialogDescription id="create-collection-description">
              Pick a name and icon for your new vocabulary collection.
            </DialogDescription>
          </DialogHeader>

          <form className="space-y-5" onSubmit={handleCreateCollection}>
            <div className="space-y-2">
              <label htmlFor="collection_name" className="text-sm font-medium text-text-primary">
                Name
              </label>
              <input
                id="collection_name"
                name="collection_name"
                value={collectionName}
                maxLength={100}
                onChange={(event) => setCollectionName(event.target.value)}
                className="flex w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary shadow-sm outline-none transition focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="TOEIC Writing"
                required
              />
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium text-text-primary">Icon</p>
              <div className="grid grid-cols-5 gap-2 sm:grid-cols-10">
                {ICON_OPTIONS.map((icon) => {
                  const isSelected = icon === collectionIcon;

                  return (
                    <button
                      key={icon}
                      type="button"
                      aria-label={`Choose ${icon}`}
                      aria-pressed={isSelected}
                      onClick={() => setCollectionIcon(icon)}
                      className={`flex h-11 items-center justify-center rounded-lg border text-xl transition-colors ${
                        isSelected
                          ? "border-zinc-700 bg-zinc-900 text-zinc-50"
                          : "border-zinc-200 bg-zinc-50 text-zinc-700 hover:bg-zinc-100"
                      }`}
                    >
                      {icon}
                    </button>
                  );
                })}
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="outline"
                disabled={createCollection.isPending || collectionName.trim().length === 0}
              >
                {createCollection.isPending ? "Creating..." : "Create Collection"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={collectionToDelete !== null}
        onOpenChange={(open) => {
          if (!open) {
            setCollectionToDelete(null);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {collectionToDelete ? `Delete '${collectionToDelete.name}'?` : "Delete collection?"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {collectionToDelete
                ? `The ${collectionToDelete.term_count} terms will remain in your library but won't be grouped.`
                : "The terms will remain in your library but won't be grouped."}
            </AlertDialogDescription>
          </AlertDialogHeader>

          <AlertDialogFooter>
            <AlertDialogCancel asChild>
              <Button type="button" variant="outline" disabled={deleteCollection.isPending}>
                Cancel
              </Button>
            </AlertDialogCancel>
            <AlertDialogAction asChild>
              <Button
                type="button"
                variant="destructive"
                disabled={deleteCollection.isPending}
                onClick={(event) => {
                  event.preventDefault();
                  void handleDeleteCollection();
                }}
              >
                {deleteCollection.isPending ? "Deleting..." : "Delete"}
              </Button>
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {selectedCollection ? (
        <AddWordsDialog
          open={isAddWordsDialogOpen}
          onOpenChange={setIsAddWordsDialogOpen}
          collectionId={selectedCollection.id}
          collectionName={selectedCollection.name}
        />
      ) : null}
    </>
  );
}
