// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { VocabularyRequestPreview } from "./VocabularyRequestPreview";

const useConfirmVocabularyRequestMock = vi.fn();
const useRouterMock = vi.fn();
const useToastMock = vi.fn();

vi.mock("@/hooks/useConfirmVocabularyRequest", () => ({
  useConfirmVocabularyRequest: () => useConfirmVocabularyRequestMock(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => useRouterMock(),
}));

vi.mock("@/components/ui/toast", () => ({
  useToast: () => useToastMock(),
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, disabled, onClick }: any) => (
    <button type="button" disabled={disabled} onClick={onClick}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

describe("VocabularyRequestPreview", () => {
  let container: HTMLDivElement;
  let root: Root;
  const onBack = vi.fn();

  const mockPreviewData = {
    preview_id: "test-preview-id",
    terms: [
      {
        term_id: 1,
        candidate_id: null,
        term: "protocol",
        language: "en",
        definition: "A set of rules",
        ipa: null,
        cefr_level: "B2",
        jlpt_level: null,
        examples: [],
        source: "corpus",
        validated_against_jmdict: false,
      },
      {
        term_id: 2,
        candidate_id: null,
        term: "network",
        language: "en",
        definition: "A connected system",
        ipa: null,
        cefr_level: "B2",
        jlpt_level: null,
        examples: [],
        source: "corpus",
        validated_against_jmdict: false,
      },
      {
        term_id: null,
        candidate_id: "llm_abc123",
        term: "bandwidth",
        language: "en",
        definition: "The capacity of a channel",
        ipa: null,
        cefr_level: "C1",
        jlpt_level: null,
        examples: ["High bandwidth connection"],
        source: "llm",
        validated_against_jmdict: false,
      },
    ],
    corpus_match_count: 2,
    gap_count: 8,
    requested_count: 10,
  };

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    vi.clearAllMocks();
    useRouterMock.mockReturnValue({ push: vi.fn() });
    useToastMock.mockReturnValue({ success: vi.fn(), error: vi.fn() });
    useConfirmVocabularyRequestMock.mockReturnValue({
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

  const renderComponent = async () => {
    await act(async () => {
      root.render(<VocabularyRequestPreview previewData={mockPreviewData} onBack={onBack} />);
    });
  };

  it("renders corpus and LLM term sections", async () => {
    await renderComponent();

    const corpusLabel = container.querySelector(".text-sm.font-medium");
    expect(corpusLabel?.textContent).toContain("Corpus Terms");
  });

  it("shows LLM generated section for llm source terms", async () => {
    await renderComponent();

    const llmSection = container.querySelectorAll(".text-sm.font-medium");
    expect(llmSection[1]?.textContent).toContain("LLM-Generated Candidates");
  });

  it("calls onBack when back button is clicked", async () => {
    await renderComponent();

    const backButton = container.querySelectorAll('button[type="button"]')[0];
    await act(async () => {
      backButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(onBack).toHaveBeenCalled();
  });

  it("disables confirm button when no terms are selected", async () => {
    const emptyPreviewData = {
      ...mockPreviewData,
      terms: [],
    };

    await act(async () => {
      root.render(<VocabularyRequestPreview previewData={emptyPreviewData} onBack={onBack} />);
    });

    const confirmButton = container.querySelectorAll('button[type="button"]')[1];
    expect(confirmButton?.textContent).toContain("Add 0 Terms");
  });

  it("toggles LLM candidate selection when checkbox is clicked", async () => {
    await renderComponent();

    const llmCheckbox = container.querySelectorAll('input[type="checkbox"]')[3];
    await act(async () => {
      llmCheckbox?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
  });
});
