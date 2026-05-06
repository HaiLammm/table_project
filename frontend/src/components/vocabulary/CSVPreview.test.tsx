// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CSVPreview } from "./CSVPreview";
import type { CSVImportPreviewResponse } from "@/types/vocabulary";

const mockPreviewData: CSVImportPreviewResponse = {
  total_rows: 3,
  valid_count: 2,
  warning_count: 1,
  error_count: 0,
  detected_columns: ["term", "language", "definition"],
  preview_rows: [
    { row_number: 1, term: "hello", language: "en", definition: "A greeting", tags: null, status: "valid", error_message: null },
    { row_number: 2, term: "<html>tag", language: "en", definition: null, tags: null, status: "warning", error_message: "Term contains HTML tags" },
    { row_number: 3, term: "goodbye", language: "en", definition: "A farewell", tags: null, status: "valid", error_message: null },
  ],
};

const onImportMock = vi.fn();
const onCancelMock = vi.fn();

describe("CSVPreview", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    vi.clearAllMocks();
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
  });

  const renderComponent = async (
    preview: CSVImportPreviewResponse,
    props = { isImporting: false, onImport: onImportMock, onCancel: onCancelMock }
  ) => {
    await act(async () => {
      root.render(<CSVPreview preview={preview} {...props} />);
    });
  };

  it("renders preview data with correct counts", async () => {
    await renderComponent(mockPreviewData);

    expect(container.textContent).toContain("2 valid");
    expect(container.textContent).toContain("1 warnings");
    expect(container.textContent).toContain("out of 3 total");
  });

  it("renders table with correct headers", async () => {
    await renderComponent(mockPreviewData);

    const headers = container.querySelectorAll("th");
    expect(headers[0].textContent).toContain("Row");
    expect(headers[1].textContent).toContain("Term");
    expect(headers[2].textContent).toContain("Language");
  });

  it("renders correct number of rows", async () => {
    await renderComponent(mockPreviewData);

    const rows = container.querySelectorAll("tbody tr");
    expect(rows.length).toBe(3);
  });

  it("shows green checkmark for valid rows", async () => {
    await renderComponent(mockPreviewData);

    const validIcon = container.querySelector(".text-green-600");
    expect(validIcon).not.toBeNull();
  });

  it("shows warning icon for warning rows", async () => {
    await renderComponent(mockPreviewData);

    const warningIcon = container.querySelector(".text-amber-500");
    expect(warningIcon).not.toBeNull();
  });

  it("calls onCancel when Cancel button is clicked", async () => {
    await renderComponent(mockPreviewData);

    const buttons = container.querySelectorAll("button");
    const cancelBtn = buttons[0];
    await act(async () => {
      cancelBtn?.click();
    });

    expect(onCancelMock).toHaveBeenCalled();
  });

  it("calls onImport when Import button is clicked", async () => {
    await renderComponent(mockPreviewData);

    const buttons = container.querySelectorAll("button");
    const importBtn = buttons[buttons.length - 1];
    await act(async () => {
      importBtn?.click();
    });

    expect(onImportMock).toHaveBeenCalled();
  });

  it("disables buttons when isImporting is true", async () => {
    await renderComponent(mockPreviewData, { ...{ isImporting: true }, ...{ onImport: onImportMock, onCancel: onCancelMock } });

    const buttons = container.querySelectorAll("button");
    buttons.forEach((btn) => {
      expect((btn as HTMLButtonElement).disabled).toBe(true);
    });
  });

  it("shows loading text in import button when importing", async () => {
    await renderComponent(mockPreviewData, { ...{ isImporting: true }, ...{ onImport: onImportMock, onCancel: onCancelMock } });

    const loadingText = container.textContent;
    expect(loadingText).toContain("Importing...");
  });
});