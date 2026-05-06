// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DataExportButton } from "./DataExportButton";

const useApiClientMock = vi.fn();
const useMutationMock = vi.fn();
const useQueryClientMock = vi.fn();
const toastSuccessMock = vi.fn();
const toastErrorMock = vi.fn();
const invalidateQueriesMock = vi.fn();

vi.mock("@/lib/api-client", () => ({
  ApiClientError: class ApiClientError extends Error {},
  useApiClient: () => useApiClientMock(),
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation: (options: unknown) => useMutationMock(options),
  useQueryClient: () => useQueryClientMock(),
}));

vi.mock("@/components/ui/toast", () => ({
  useToast: () => ({
    success: toastSuccessMock,
    error: toastErrorMock,
  }),
}));

describe("DataExportButton", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    useApiClientMock.mockReturnValue(vi.fn());
    useQueryClientMock.mockReturnValue({
      invalidateQueries: invalidateQueriesMock,
    });
    useMutationMock.mockImplementation(() => ({
      mutate: vi.fn(),
      isPending: false,
    }));
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    vi.clearAllMocks();
  });

  it("requests a data export when clicked", async () => {
    const mutateMock = vi.fn();

    useMutationMock.mockImplementation(() => ({
      mutate: mutateMock,
      isPending: false,
    }));

    await act(async () => {
      root.render(<DataExportButton />);
    });

    await act(async () => {
      const button = Array.from(container.querySelectorAll("button")).find((element) =>
        element.textContent?.includes("Request export"),
      );
      button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(mutateMock).toHaveBeenCalledTimes(1);
  });

  it("shows a success toast and invalidates export queries after success", async () => {
    let mutationOptions:
      | {
          onSuccess?: () => void | Promise<void>;
          onError?: (error: Error) => void | Promise<void>;
        }
      | undefined;

    useMutationMock.mockImplementation((options) => {
      mutationOptions = options as typeof mutationOptions;
      return {
        mutate: vi.fn(),
        isPending: false,
      };
    });

    await act(async () => {
      root.render(<DataExportButton />);
    });

    await act(async () => {
      await mutationOptions?.onSuccess?.();
    });

    expect(toastSuccessMock).toHaveBeenCalledWith("Export requested. You'll be notified when ready.");
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: ["user", "data-export"],
    });
  });

  it("shows an error toast when the export request fails", async () => {
    let mutationOptions:
      | {
          onSuccess?: () => void | Promise<void>;
          onError?: (error: Error) => void | Promise<void>;
        }
      | undefined;

    useMutationMock.mockImplementation((options) => {
      mutationOptions = options as typeof mutationOptions;
      return {
        mutate: vi.fn(),
        isPending: false,
      };
    });

    await act(async () => {
      root.render(<DataExportButton />);
    });

    await act(async () => {
      await mutationOptions?.onError?.(new Error("Export failed"));
    });

    expect(toastErrorMock).toHaveBeenCalledWith("Export failed");
  });
});
