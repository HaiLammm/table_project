// @vitest-environment jsdom

import { act } from "react";
import { createRoot } from "react-dom/client";
import type { Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { UpcomingSchedule } from "./UpcomingSchedule";
import type { ScheduleBucketResponse } from "@/types/srs";

describe("UpcomingSchedule", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      false;
  });

  it("renders tomorrow and this week stat chips with correct values", async () => {
    const tomorrow: ScheduleBucketResponse = { due_count: 12, estimated_minutes: 2 };
    const thisWeek: ScheduleBucketResponse = { due_count: 45, estimated_minutes: 8 };

    await act(async () => {
      root.render(<UpcomingSchedule tomorrow={tomorrow} thisWeek={thisWeek} />);
    });

    expect(container.textContent).toContain("Tomorrow");
    expect(container.textContent).toContain("12 cards");
    expect(container.textContent).toContain("~2 min");
    expect(container.textContent).toContain("This week");
    expect(container.textContent).toContain("45 cards");
    expect(container.textContent).toContain("~8 min");
  });

  it("renders loading skeleton when isLoading is true", async () => {
    const tomorrow: ScheduleBucketResponse = { due_count: 0, estimated_minutes: 0 };
    const thisWeek: ScheduleBucketResponse = { due_count: 0, estimated_minutes: 0 };

    await act(async () => {
      root.render(<UpcomingSchedule tomorrow={tomorrow} thisWeek={thisWeek} isLoading={true} />);
    });

    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("displays zero counts correctly", async () => {
    const tomorrow: ScheduleBucketResponse = { due_count: 0, estimated_minutes: 0 };
    const thisWeek: ScheduleBucketResponse = { due_count: 0, estimated_minutes: 0 };

    await act(async () => {
      root.render(<UpcomingSchedule tomorrow={tomorrow} thisWeek={thisWeek} />);
    });

    expect(container.textContent).toContain("0 cards");
    expect(container.textContent).toContain("0 min");
  });
});