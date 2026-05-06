// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AddTermForm } from "./AddTermForm";

const useCreateVocabularyTermMock = vi.fn();
const useToastMock = vi.fn();
const useQueryClientMock = vi.fn();

vi.mock("@/hooks/useCreateVocabularyTerm", () => ({
  useCreateVocabularyTerm: () => useCreateVocabularyTermMock(),
}));

vi.mock("@/components/ui/toast", () => ({
  useToast: () => useToastMock(),
}));

vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => useQueryClientMock(),
  useMutation: (options: any) => options,
  useQuery: () => ({ isLoading: false, isError: false, data: null }),
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/components/vocabulary/TermAutoSuggest", () => ({
  TermAutoSuggest: ({ value, onChange, onSelect, onCreateNew }: any) => (
    <div data-testid="term-autosuggest">
      <input
        type="text"
        value={value}
        onChange={(e: any) => onChange(e.target.value)}
        onKeyDown={(e: any) => {
          if (e.key === "Enter") {
            onCreateNew();
          }
        }}
      />
      <button type="button" onClick={() => onCreateNew()}>
        Create New
      </button>
    </div>
  ),
}));

describe("AddTermForm", () => {
  let container: HTMLDivElement;
  let root: Root;
  const onTermCreated = vi.fn();

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    vi.clearAllMocks();
    useToastMock.mockReturnValue({ success: vi.fn(), error: vi.fn() });
    useCreateVocabularyTermMock.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      false;
  });

  const renderComponent = async (props = {}) => {
    await act(async () => {
      root.render(<AddTermForm {...props} />);
    });
  };

  it("renders form with term input, language select, and submit button", async () => {
    await renderComponent();

    const termInput = container.querySelector('input[type="text"]');
    expect(termInput).not.toBeNull();

    const languageSelect = container.querySelector("select");
    expect(languageSelect).not.toBeNull();

    const submitButton = container.querySelector('button[type="submit"]');
    expect(submitButton).not.toBeNull();
    expect(submitButton?.textContent).toContain("Add Term");
  });

  it("shows optional definition link when rendered", async () => {
    await renderComponent();

    const addDefLink = container.querySelector('button[type="button"]');
    expect(addDefLink?.textContent).toContain("Add definition");
  });

  it("toggles definition textarea when clicking add definition link", async () => {
    await renderComponent();

    const addDefLink = container.querySelector('button[type="button"]');
    await act(async () => {
      addDefLink?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    const textarea = container.querySelector("textarea");
    expect(textarea).not.toBeNull();
  });

  it("shows inline error when term already exists", async () => {
    useCreateVocabularyTermMock.mockReturnValueOnce({
      mutate: vi.fn((_data: any, options: any) => {
        options.onError({
          code: "DUPLICATE_TERM",
          message: "This term already exists in your vocabulary",
        } as any);
      }),
      isPending: false,
    });

    await renderComponent();

    const termInput = container.querySelector('input[type="text"]') as HTMLInputElement;
    await act(async () => {
      termInput.value = "existing_term";
      termInput.dispatchEvent(new Event("input", { bubbles: true }));
    });

    const form = container.querySelector("form");
    await act(async () => {
      form?.dispatchEvent(new Event("submit", { bubbles: true }));
    });

    const errorMsg = container.querySelector(".text-red-600");
    expect(errorMsg?.textContent).toContain("This term already exists in your vocabulary");
  });

  it("shows success toast when term is created", async () => {
    const mockTerm = {
      id: 1,
      term: "new_term",
      language: "en",
      parent_id: null,
      cefr_level: null,
      jlpt_level: null,
      part_of_speech: null,
      definitions: [],
      created_at: null,
    };

    const successToast = vi.fn();
    useToastMock.mockReturnValueOnce({ success: successToast, error: vi.fn() });

    useCreateVocabularyTermMock.mockReturnValueOnce({
      mutate: vi.fn((_data: any, options: any) => {
        options.onSuccess(mockTerm);
      }),
      isPending: false,
    });

    await renderComponent();

    const form = container.querySelector("form");
    await act(async () => {
      form?.dispatchEvent(new Event("submit", { bubbles: true }));
    });

    expect(successToast).toHaveBeenCalledWith("Term added — enriching...");
  });

  it("clears form after successful creation", async () => {
    const mockTerm = {
      id: 1,
      term: "new_term",
      language: "en",
      parent_id: null,
      cefr_level: null,
      jlpt_level: null,
      part_of_speech: null,
      definitions: [],
      created_at: null,
    };

    useCreateVocabularyTermMock.mockReturnValueOnce({
      mutate: vi.fn((_data: any, options: any) => {
        options.onSuccess(mockTerm);
      }),
      isPending: false,
    });

    await renderComponent();

    const termInput = container.querySelector('input[type="text"]') as HTMLInputElement;
    await act(async () => {
      termInput.value = "new_term";
      termInput.dispatchEvent(new Event("input", { bubbles: true }));
    });

    const form = container.querySelector("form");
    await act(async () => {
      form?.dispatchEvent(new Event("submit", { bubbles: true }));
    });

    const inputAfterSubmit = container.querySelector('input[type="text"]') as HTMLInputElement;
    expect(inputAfterSubmit.value).toBe("");
  });

  it("disables submit button while pending", async () => {
    useCreateVocabularyTermMock.mockReturnValueOnce({
      mutate: vi.fn(),
      isPending: true,
    });

    await renderComponent();

    const submitButton = container.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(submitButton.disabled).toBe(true);
  });
});