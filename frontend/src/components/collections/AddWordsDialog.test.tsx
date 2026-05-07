// @vitest-environment jsdom

import { act, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AddWordsDialog } from "./AddWordsDialog";

const addTermMutateAsyncMock = vi.fn();
const addTermsBulkMutateAsyncMock = vi.fn();
const importCSVMutateAsyncMock = vi.fn();
const importPreviewMutateAsyncMock = vi.fn();
const toastSuccessMock = vi.fn();
const toastErrorMock = vi.fn();
const useVocabularySearchMock = vi.fn();

vi.mock("@/hooks/useCollections", () => ({
  useAddTermToCollection: () => ({
    mutateAsync: addTermMutateAsyncMock,
    isPending: false,
  }),
  useAddTermsBulk: () => ({
    mutateAsync: addTermsBulkMutateAsyncMock,
    isPending: false,
  }),
  useImportCSVToCollection: () => ({
    mutateAsync: importCSVMutateAsyncMock,
    isPending: false,
  }),
}));

vi.mock("@/hooks/useCSVImport", () => ({
  useCSVImportPreview: () => ({
    mutateAsync: importPreviewMutateAsyncMock,
    isPending: false,
  }),
}));

vi.mock("@/hooks/useVocabularySearch", () => ({
  useVocabularySearch: (query: string) => useVocabularySearchMock(query),
}));

vi.mock("@/components/ui/toast", () => ({
  useToast: () => ({
    success: toastSuccessMock,
    error: toastErrorMock,
  }),
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
    DialogHeader: PassThrough,
    DialogTitle: PassThrough,
  };
});

vi.mock("@/components/vocabulary/CSVImporter", () => ({
  CSVImporter: ({ onFileSelected }: { onFileSelected: (file: File) => void }) => (
    <button type="button" onClick={() => onFileSelected(new File(["term"], "terms.csv"))}>
      preview-csv
    </button>
  ),
}));

vi.mock("@/components/vocabulary/CSVPreview", () => ({
  CSVPreview: () => <div>csv-preview</div>,
}));

describe("AddWordsDialog", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    addTermMutateAsyncMock.mockResolvedValue({ added: 1, skipped: 0 });
    addTermsBulkMutateAsyncMock.mockResolvedValue({ added: 1, skipped: 0 });
    importCSVMutateAsyncMock.mockResolvedValue({ added: 1, skipped: 0, errors: [] });
    importPreviewMutateAsyncMock.mockResolvedValue({
      total_rows: 1,
      valid_count: 1,
      warning_count: 0,
      error_count: 0,
      preview_rows: [],
      detected_columns: ["term"],
    });
    useVocabularySearchMock.mockImplementation((query: string) => ({
      data:
        query === "pro"
          ? {
              items: [
                {
                  id: 11,
                  term: "protocol",
                  language: "en",
                  parent_id: null,
                  cefr_level: "B2",
                  jlpt_level: null,
                  part_of_speech: "noun",
                  definitions: [],
                  created_at: null,
                },
              ],
            }
          : { items: [] },
      isLoading: false,
    }));
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

  it("renders the three add-word tabs", async () => {
    await act(async () => {
      root.render(
        <AddWordsDialog
          open
          onOpenChange={() => undefined}
          collectionId={1}
          collectionName="Backend"
        />,
      );
    });

    expect(container.textContent).toContain("Manual");
    expect(container.textContent).toContain("Import CSV");
    expect(container.textContent).toContain("Browse Corpus");
  });

  it("adds a suggested term from the manual tab", async () => {
    await act(async () => {
      root.render(
        <AddWordsDialog
          open
          onOpenChange={() => undefined}
          collectionId={1}
          collectionName="Backend"
        />,
      );
    });

    await act(async () => {
      const input = container.querySelector("#manual-term-search") as HTMLInputElement;
      const valueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
      valueSetter?.call(input, "pro");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });

    await act(async () => {
      const resultButton = Array.from(container.querySelectorAll("button")).find((element) =>
        element.textContent?.includes("protocol"),
      );
      resultButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(addTermMutateAsyncMock).toHaveBeenCalledWith({ term_id: 11 });
  });
});
