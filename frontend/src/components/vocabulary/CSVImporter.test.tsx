// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CSVImporter } from "./CSVImporter";

const onFileSelectedMock = vi.fn();

describe("CSVImporter", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    vi.clearAllMocks();
    onFileSelectedMock.mockClear();
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
  });

  const renderComponent = async (props: { onFileSelected?: (file: File) => void; isLoading?: boolean } = {}) => {
    await act(async () => {
      root.render(<CSVImporter onFileSelected={props.onFileSelected || onFileSelectedMock} isLoading={props.isLoading} />);
    });
  };

  it("renders drop zone with upload icon and text", async () => {
    await renderComponent();

    const uploadIcon = container.querySelector("svg");
    expect(uploadIcon).not.toBeNull();

    const text = container.textContent;
    expect(text).toContain("Drop CSV file here or click to browse");
    expect(text).toContain("Supports .csv, .tsv, .txt up to 10MB");
  });

  it("renders file input with correct accept attribute", async () => {
    await renderComponent();

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).not.toBeNull();
    expect(fileInput.accept).toBe(".csv,.tsv,.txt");
  });

  it("shows loading state when isLoading is true", async () => {
    await renderComponent({ isLoading: true });

    const loading = container.textContent;
    expect(loading).toContain("Parsing file...");
  });

  it("hides file input when loading", async () => {
    await renderComponent({ isLoading: true });

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput.disabled).toBe(true);
  });
});