// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PreferencesForm, type UserPreferences } from "./PreferencesForm";

const useApiClientMock = vi.fn();
const useQueryMock = vi.fn();
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
  useQuery: (options: unknown) => useQueryMock(options),
  useMutation: (options: unknown) => useMutationMock(options),
  useQueryClient: () => useQueryClientMock(),
}));

vi.mock("@/components/ui/toast", () => ({
  useToast: () => ({
    success: toastSuccessMock,
    error: toastErrorMock,
  }),
}));

const basePreferences: UserPreferences = {
  learning_goal: "general",
  english_level: "beginner",
  japanese_level: "none",
  daily_study_minutes: 15,
  it_domain: "general_it",
  notification_email: true,
  notification_review_reminder: true,
};

describe("PreferencesForm", () => {
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
    useQueryMock.mockReturnValue({
      data: basePreferences,
      isPending: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
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

  it("renders fetched preferences into the form", async () => {
    await act(async () => {
      root.render(<PreferencesForm />);
    });

    expect(container.textContent).toContain("Learning goal");
    expect((container.querySelector("#learning_goal") as HTMLSelectElement).value).toBe("general");
    expect((container.querySelector("#english_level") as HTMLSelectElement).value).toBe("beginner");
    expect((container.querySelector("#daily_study_minutes") as HTMLSelectElement).value).toBe("15");
  });

  it("submits updated preferences and shows a success toast", async () => {
    const mutateMock = vi.fn();
    let mutationOptions:
      | {
          onSuccess?: (updatedPreferences: UserPreferences) => void | Promise<void>;
          onError?: (error: Error) => void | Promise<void>;
        }
      | undefined;

    useMutationMock.mockImplementation((options) => {
      mutationOptions = options as typeof mutationOptions;
      return {
        mutate: mutateMock,
        isPending: false,
      };
    });

    await act(async () => {
      root.render(<PreferencesForm />);
    });

    await act(async () => {
      const dailyStudySelect = container.querySelector("#daily_study_minutes") as HTMLSelectElement;
      dailyStudySelect.value = "30";
      dailyStudySelect.dispatchEvent(new Event("change", { bubbles: true }));
    });

    await act(async () => {
      const form = container.querySelector("form");
      form?.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    });

    expect(mutateMock).toHaveBeenCalledWith({
      ...basePreferences,
      daily_study_minutes: 30,
    });

    await act(async () => {
      await mutationOptions?.onSuccess?.({
        ...basePreferences,
        daily_study_minutes: 30,
      });
    });

    expect(toastSuccessMock).toHaveBeenCalledWith("Settings updated");
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: ["user", "preferences"],
    });
  });

  it("shows an error toast when the save mutation fails", async () => {
    let mutationOptions:
      | {
          onSuccess?: (updatedPreferences: UserPreferences) => void | Promise<void>;
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
      root.render(<PreferencesForm />);
    });

    await act(async () => {
      await mutationOptions?.onError?.(new Error("Save failed"));
    });

    expect(toastErrorMock).toHaveBeenCalledWith("Save failed");
  });
});
