// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CollectionCard } from "./CollectionCard";

vi.mock("@/components/ui/dropdown-menu", async () => {
  const React = await import("react");

  function PassThrough({ children }: { children: React.ReactNode }) {
    return <>{children}</>;
  }

  return {
    DropdownMenu: PassThrough,
    DropdownMenuContent: PassThrough,
    DropdownMenuSeparator: () => <hr />,
    DropdownMenuTrigger: PassThrough,
    DropdownMenuItem: ({
      children,
      onSelect,
      className,
    }: {
      children: React.ReactNode;
      onSelect?: (event: { preventDefault: () => void }) => void;
      className?: string;
    }) => (
      <button
        type="button"
        className={className}
        onClick={() => onSelect?.({ preventDefault: () => undefined })}
      >
        {children}
      </button>
    ),
  };
});

describe("CollectionCard", () => {
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
    vi.clearAllMocks();
  });

  it("renders the default card metrics", async () => {
    await act(async () => {
      root.render(
        <CollectionCard
          icon="📚"
          name="TOEIC"
          termCount={8}
          masteryPercent={63}
          onClick={() => undefined}
        />,
      );
    });

    expect(container.textContent).toContain("TOEIC");
    expect(container.textContent).toContain("8 terms");
    expect(container.textContent).toContain("63%");
    expect(container.querySelector('[style="width: 63%;"]')).not.toBeNull();
  });

  it("renders the create variant call to action", async () => {
    await act(async () => {
      root.render(
        <CollectionCard
          icon="+"
          name="New Collection"
          termCount={0}
          masteryPercent={0}
          variant="create"
          onClick={() => undefined}
        />,
      );
    });

    expect(container.textContent).toContain("+ New Collection");
    expect(container.textContent).toContain("Start grouping terms by topic or project");
  });

  it("submits inline rename on Enter", async () => {
    const onRename = vi.fn().mockResolvedValue(undefined);

    await act(async () => {
      root.render(
        <CollectionCard
          icon="💻"
          name="Backend"
          termCount={4}
          masteryPercent={50}
          onClick={() => undefined}
          onRename={onRename}
        />,
      );
    });

    await act(async () => {
      const nameButton = Array.from(container.querySelectorAll("button")).find(
        (element) => element.textContent === "Backend",
      );
      nameButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    const input = container.querySelector('input[aria-label="Collection name"]') as HTMLInputElement;

    await act(async () => {
      const valueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
      valueSetter?.call(input, "Backend API");
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    });

    expect(onRename).toHaveBeenCalledWith("Backend API");
  });

  it("cancels inline rename on Escape", async () => {
    const onRename = vi.fn();

    await act(async () => {
      root.render(
        <CollectionCard
          icon="🌍"
          name="Networking"
          termCount={3}
          masteryPercent={40}
          onClick={() => undefined}
          onRename={onRename}
        />,
      );
    });

    await act(async () => {
      const nameButton = Array.from(container.querySelectorAll("button")).find(
        (element) => element.textContent === "Networking",
      );
      nameButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    const input = container.querySelector('input[aria-label="Collection name"]') as HTMLInputElement;

    await act(async () => {
      const valueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
      valueSetter?.call(input, "Networking Core");
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    });

    expect(onRename).not.toHaveBeenCalled();
    expect(container.textContent).toContain("Networking");
  });

  it("calls onDelete from the actions menu", async () => {
    const onDelete = vi.fn();

    await act(async () => {
      root.render(
        <CollectionCard
          icon="💼"
          name="Work"
          termCount={2}
          masteryPercent={75}
          onClick={() => undefined}
          onDelete={onDelete}
        />,
      );
    });

    await act(async () => {
      const deleteButton = Array.from(container.querySelectorAll("button")).find(
        (element) => element.textContent === "Delete",
      );
      deleteButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(onDelete).toHaveBeenCalledTimes(1);
  });
});
