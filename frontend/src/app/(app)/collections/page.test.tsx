// @vitest-environment jsdom

import { act, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import CollectionsPage from "./page";

const useCollectionsMock = vi.fn();
const useCollectionTermsMock = vi.fn();
const createMutateAsyncMock = vi.fn();
const updateMutateAsyncMock = vi.fn();
const deleteMutateAsyncMock = vi.fn();
const removeTermMutateAsyncMock = vi.fn();
const addTermMutateAsyncMock = vi.fn();
const toastErrorMock = vi.fn();
const toastShowUndoMock = vi.fn();

vi.mock("@/hooks/useCollections", () => ({
  useCollections: () => useCollectionsMock(),
  useCollectionTerms: () => useCollectionTermsMock(),
  useCreateCollection: () => ({
    mutateAsync: createMutateAsyncMock,
    isPending: false,
  }),
  useUpdateCollection: () => ({
    mutateAsync: updateMutateAsyncMock,
    isPending: false,
  }),
  useDeleteCollection: () => ({
    mutateAsync: deleteMutateAsyncMock,
    isPending: false,
  }),
  useRemoveTermFromCollection: () => ({
    mutateAsync: removeTermMutateAsyncMock,
    isPending: false,
  }),
  useAddTermToCollection: () => ({
    mutateAsync: addTermMutateAsyncMock,
    isPending: false,
  }),
}));

vi.mock("@/components/ui/toast", () => ({
  useToast: () => ({
    error: toastErrorMock,
    showUndoToast: toastShowUndoMock,
  }),
}));

vi.mock("next/link", () => ({
  default: ({ children }: { children: ReactNode }) => children,
}));

vi.mock("@/components/collections", async () => {
  const React = await import("react");

  return {
    CollectionCard: ({
      name,
      variant,
      onClick,
      onDelete,
    }: {
      name: string;
      variant?: "default" | "create";
      onClick: () => void;
      onDelete?: () => void;
    }) => (
      <div>
        <button type="button" onClick={onClick}>
          {variant === "create" ? "create-card" : name}
        </button>
        {onDelete ? (
          <button type="button" onClick={onDelete}>
            delete-{name}
          </button>
        ) : null}
      </div>
    ),
  };
});

vi.mock("@/components/collections/AddWordsDialog", () => ({
  AddWordsDialog: ({ open }: { open: boolean }) => (open ? <div>add-words-dialog</div> : null),
}));

vi.mock("@/components/ui/dialog", async () => {
  const React = await import("react");

  function Dialog({ open, children }: { open: boolean; children: ReactNode }) {
    return open ? <>{children}</> : null;
  }

  function PassThrough({ children }: { children: ReactNode }) {
    return <>{children}</>;
  }

  return {
    Dialog,
    DialogContent: PassThrough,
    DialogDescription: PassThrough,
    DialogFooter: PassThrough,
    DialogHeader: PassThrough,
    DialogTitle: PassThrough,
  };
});

vi.mock("@/components/ui/alert-dialog", async () => {
  const React = await import("react");

  function AlertDialog({ open, children }: { open: boolean; children: ReactNode }) {
    return open ? <>{children}</> : null;
  }

  function PassThrough({ children }: { children: ReactNode }) {
    return <>{children}</>;
  }

  return {
    AlertDialog,
    AlertDialogAction: PassThrough,
    AlertDialogCancel: PassThrough,
    AlertDialogContent: PassThrough,
    AlertDialogDescription: PassThrough,
    AlertDialogFooter: PassThrough,
    AlertDialogHeader: PassThrough,
    AlertDialogTitle: PassThrough,
  };
});

describe("CollectionsPage", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    createMutateAsyncMock.mockResolvedValue(undefined);
    updateMutateAsyncMock.mockResolvedValue(undefined);
    deleteMutateAsyncMock.mockResolvedValue(undefined);
    removeTermMutateAsyncMock.mockResolvedValue(undefined);
    addTermMutateAsyncMock.mockResolvedValue(undefined);
    useCollectionTermsMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        has_next: false,
      },
      refetch: vi.fn(),
    });
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      false;
    vi.clearAllMocks();
  });

  it("renders the empty state when no collections exist", async () => {
    useCollectionsMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { items: [] },
      refetch: vi.fn(),
    });

    await act(async () => {
      root.render(<CollectionsPage />);
    });

    expect(container.textContent).toContain("No collections yet");
    expect(container.textContent).toContain("+ New Collection");
  });

  it("renders the collections grid with the create card", async () => {
    useCollectionsMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            id: 1,
            name: "Backend",
            icon: "💻",
            term_count: 4,
            mastery_percent: 50,
            created_at: null,
            updated_at: null,
          },
          {
            id: 2,
            name: "Networking",
            icon: "🌍",
            term_count: 3,
            mastery_percent: 33,
            created_at: null,
            updated_at: null,
          },
        ],
      },
      refetch: vi.fn(),
    });

    await act(async () => {
      root.render(<CollectionsPage />);
    });

    expect(container.textContent).toContain("Backend");
    expect(container.textContent).toContain("Networking");
    expect(container.textContent).toContain("create-card");
  });

  it("submits the create collection flow", async () => {
    useCollectionsMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { items: [] },
      refetch: vi.fn(),
    });

    await act(async () => {
      root.render(<CollectionsPage />);
    });

    await act(async () => {
      const openButton = Array.from(container.querySelectorAll("button")).find(
        (element) => element.textContent?.includes("+ New Collection"),
      );
      openButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    await act(async () => {
      const input = container.querySelector("#collection_name") as HTMLInputElement;
      const valueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
      valueSetter?.call(input, "TOEIC Writing");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });

    await act(async () => {
      const submitButton = Array.from(container.querySelectorAll("button")).find(
        (element) => element.textContent === "Create Collection",
      );
      submitButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(createMutateAsyncMock).toHaveBeenCalledWith({
      name: "TOEIC Writing",
      icon: "📚",
    });
  });

  it("opens delete confirmation and deletes the selected collection", async () => {
    useCollectionsMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            id: 7,
            name: "Work",
            icon: "💼",
            term_count: 2,
            mastery_percent: 50,
            created_at: null,
            updated_at: null,
          },
        ],
      },
      refetch: vi.fn(),
    });

    await act(async () => {
      root.render(<CollectionsPage />);
    });

    await act(async () => {
      const deleteButton = Array.from(container.querySelectorAll("button")).find(
        (element) => element.textContent === "delete-Work",
      );
      deleteButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(container.textContent).toContain("Delete 'Work'?");
    expect(container.textContent).toContain(
      "The 2 terms will remain in your library but won't be grouped.",
    );

    await act(async () => {
      const confirmButton = Array.from(container.querySelectorAll("button")).find(
        (element) => element.textContent === "Delete",
      );
      confirmButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(deleteMutateAsyncMock).toHaveBeenCalledWith(7);
  });

  it("opens a collection detail view and renders its terms", async () => {
    useCollectionsMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            id: 1,
            name: "Backend",
            icon: "💻",
            term_count: 1,
            mastery_percent: 50,
            created_at: null,
            updated_at: null,
          },
        ],
      },
      refetch: vi.fn(),
    });
    useCollectionTermsMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            term_id: 101,
            term: "protocol",
            language: "en",
            mastery_status: "learning",
            added_at: null,
            cefr_level: "B2",
            jlpt_level: null,
            part_of_speech: "noun",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        has_next: false,
      },
      refetch: vi.fn(),
    });

    await act(async () => {
      root.render(<CollectionsPage />);
    });

    await act(async () => {
      const openButton = Array.from(container.querySelectorAll("button")).find(
        (element) => element.textContent === "Backend",
      );
      openButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(container.textContent).toContain("Back to collections");
    expect(container.textContent).toContain("protocol");
    expect(container.textContent).toContain("Add Words");
  });

  it("shows an undo toast after removing a term", async () => {
    useCollectionsMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            id: 1,
            name: "Backend",
            icon: "💻",
            term_count: 1,
            mastery_percent: 50,
            created_at: null,
            updated_at: null,
          },
        ],
      },
      refetch: vi.fn(),
    });
    useCollectionTermsMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            term_id: 101,
            term: "protocol",
            language: "en",
            mastery_status: "learning",
            added_at: null,
            cefr_level: "B2",
            jlpt_level: null,
            part_of_speech: "noun",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        has_next: false,
      },
      refetch: vi.fn(),
    });

    await act(async () => {
      root.render(<CollectionsPage />);
    });

    await act(async () => {
      const openButton = Array.from(container.querySelectorAll("button")).find(
        (element) => element.textContent === "Backend",
      );
      openButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    await act(async () => {
      const removeButton = container.querySelector(
        'button[aria-label="Remove protocol from collection"]',
      );
      removeButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(removeTermMutateAsyncMock).toHaveBeenCalledWith(101);
    expect(toastShowUndoMock).toHaveBeenCalledWith(
      expect.objectContaining({
        message: "Term removed from collection",
        action: expect.objectContaining({ label: "Undo" }),
      }),
    );
  });
});
