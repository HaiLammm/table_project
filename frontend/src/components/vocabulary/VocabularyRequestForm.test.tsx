// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { VocabularyRequestForm } from "./VocabularyRequestForm";

const useVocabularyRequestMock = vi.fn();

vi.mock("@/hooks/useVocabularyRequest", () => ({
  useVocabularyRequest: () => useVocabularyRequestMock(),
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, disabled }: any) => (
    <button type="submit" disabled={disabled}>
      {children}
    </button>
  ),
}));

describe("VocabularyRequestForm", () => {
  let container: HTMLDivElement;
  let root: Root;
  const onPreview = vi.fn();

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    vi.clearAllMocks();
    useVocabularyRequestMock.mockReturnValue({
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
      root.render(<VocabularyRequestForm onPreview={onPreview} />);
    });
  };

  it("renders form with topic input, language select, level select, count input, and submit button", async () => {
    await renderComponent();

    const topicInput = container.querySelector('input[id="topic-input"]');
    expect(topicInput).not.toBeNull();

    const languageSelect = container.querySelector('select[id="language-select"]');
    expect(languageSelect).not.toBeNull();

    const levelSelect = container.querySelector('select[id="level-select"]');
    expect(levelSelect).not.toBeNull();

    const countInput = container.querySelector('input[id="count-input"]');
    expect(countInput).not.toBeNull();

    const submitButton = container.querySelector('button[type="submit"]');
    expect(submitButton).not.toBeNull();
    expect(submitButton?.textContent).toContain("Generate Preview");
  });

  it("shows validation error when topic is empty on blur", async () => {
    await renderComponent();

    const topicInput = container.querySelector('input[id="topic-input"]') as HTMLInputElement;
    await act(async () => {
      topicInput.dispatchEvent(new FocusEvent("blur", { bubbles: true }));
    });

    const errorMsg = container.querySelector(".text-red-500");
    expect(errorMsg?.textContent).toContain("Topic is required");
  });

  it("calls preview mutation when form is submitted with valid data", async () => {
    await renderComponent();

    const topicInput = container.querySelector('input[id="topic-input"]') as HTMLInputElement;
    await act(async () => {
      topicInput.value = "networking";
      topicInput.dispatchEvent(new Event("input", { bubbles: true }));
    });

    const levelSelect = container.querySelector('select[id="level-select"]') as HTMLSelectElement;
    await act(async () => {
      levelSelect.value = "B2";
      levelSelect.dispatchEvent(new Event("change", { bubbles: true }));
    });

    const form = container.querySelector("form");
    await act(async () => {
      form?.dispatchEvent(new Event("submit", { bubbles: true }));
    });

    expect(useVocabularyRequestMock().mutate).toHaveBeenCalledWith(
      expect.objectContaining({
        topic: "networking",
        language: "en",
        level: "B2",
        count: 10,
      }),
      expect.any(Object)
    );
  });

  it("disables submit button while pending", async () => {
    useVocabularyRequestMock.mockReturnValueOnce({
      mutate: vi.fn(),
      isPending: true,
    });

    await renderComponent();

    const submitButton = container.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(submitButton.disabled).toBe(true);
  });

  it("changes level options when language is changed to Japanese", async () => {
    await renderComponent();

    const languageSelect = container.querySelector('select[id="language-select"]') as HTMLSelectElement;
    await act(async () => {
      languageSelect.value = "jp";
      languageSelect.dispatchEvent(new Event("change", { bubbles: true }));
    });

    const levelSelect = container.querySelector('select[id="level-select"]') as HTMLSelectElement;
    const options = Array.from(levelSelect.options).map((o) => o.value);

    expect(options).toContain("N5");
    expect(options).toContain("N1");
    expect(options).not.toContain("A1");
  });
});