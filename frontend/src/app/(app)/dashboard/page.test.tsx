// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DashboardPage from "./page";

const useApiClientMock = vi.fn();
const useQueryMock = vi.fn();

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@/lib/api-client", () => ({
  useApiClient: () => useApiClientMock(),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: (options: unknown) => useQueryMock(options),
}));

describe("DashboardPage", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(async () => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    const { useReviewStore } = await import("@/stores/review-store");
    useReviewStore.setState({ queueMode: "full" });
    useApiClientMock.mockReturnValue(vi.fn());
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

  it("renders the empty state when no cards are due", async () => {
    useQueryMock.mockImplementation((options) => {
      const queryKey = JSON.stringify((options as { queryKey: unknown[] }).queryKey);
      if (queryKey === JSON.stringify(["srs", "queue-stats"])) {
        return {
          isLoading: false,
          isError: false,
          isSuccess: true,
          data: {
            due_count: 0,
            estimated_minutes: 0,
            has_overdue: false,
            overdue_count: 0,
          },
        };
      }

      return {
        isLoading: false,
        isError: false,
        isSuccess: false,
        data: undefined,
      };
    });

    await act(async () => {
      root.render(<DashboardPage />);
    });

    expect(container.textContent).toContain("All caught up!");
    expect(container.textContent).toContain(
      "No cards due for review. Come back tomorrow or add new words.",
    );
    expect(container.textContent).toContain("Add Words");
  });
});
