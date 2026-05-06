// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DeleteAccountDialog } from "./DeleteAccountDialog";

const useApiClientMock = vi.fn();
const useMutationMock = vi.fn();
const useClerkMock = vi.fn();
const useUserMock = vi.fn();
const routerPushMock = vi.fn();
const toastErrorMock = vi.fn();
const signOutMock = vi.fn();

vi.mock("@/lib/api-client", () => ({
  ApiClientError: class ApiClientError extends Error {},
  useApiClient: () => useApiClientMock(),
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation: (options: unknown) => useMutationMock(options),
}));

vi.mock("@clerk/nextjs", () => ({
  useClerk: () => useClerkMock(),
  useUser: () => useUserMock(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: routerPushMock,
  }),
}));

vi.mock("@/components/ui/toast", () => ({
  useToast: () => ({
    error: toastErrorMock,
  }),
}));

vi.mock("@/components/ui/alert-dialog", async () => {
  const React = await import("react");

  function PassThrough({ children }: { children: React.ReactNode }) {
    return <>{children}</>;
  }

  return {
    AlertDialog: PassThrough,
    AlertDialogAction: PassThrough,
    AlertDialogCancel: PassThrough,
    AlertDialogContent: PassThrough,
    AlertDialogDescription: PassThrough,
    AlertDialogFooter: PassThrough,
    AlertDialogHeader: PassThrough,
    AlertDialogTitle: PassThrough,
    AlertDialogTrigger: PassThrough,
  };
});

describe("DeleteAccountDialog", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
      true;
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    useApiClientMock.mockReturnValue(vi.fn());
    useClerkMock.mockReturnValue({
      signOut: signOutMock,
    });
    useUserMock.mockReturnValue({
      user: {
        primaryEmailAddress: {
          emailAddress: "lem@example.com",
        },
        emailAddresses: [{ emailAddress: "lem@example.com" }],
      },
    });
    useMutationMock.mockImplementation(() => ({
      mutate: vi.fn(),
      isPending: false,
    }));
    signOutMock.mockResolvedValue(undefined);
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

  it("keeps the destructive action disabled until the email matches", async () => {
    await act(async () => {
      root.render(<DeleteAccountDialog />);
    });

    expect(
      (
        Array.from(container.querySelectorAll("button")).find(
          (element) =>
            element.textContent?.includes("Delete account") &&
            element.className.includes("bg-red-600"),
        ) as HTMLButtonElement
      ).disabled,
    ).toBe(true);

    await act(async () => {
      const input = container.querySelector("#confirmation_email") as HTMLInputElement;
      const valueSetter = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )?.set;
      valueSetter?.call(input, "lem@example.com");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });

    const destructiveButton = Array.from(container.querySelectorAll("button")).find(
      (element) =>
        element.textContent?.includes("Delete account") && element.className.includes("bg-red-600"),
    ) as HTMLButtonElement;

    expect(destructiveButton.disabled).toBe(false);
  });

  it("submits deletion, signs out, and redirects on success", async () => {
    const mutateMock = vi.fn();
    let mutationOptions:
      | {
          onSuccess?: () => void | Promise<void>;
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
      root.render(<DeleteAccountDialog />);
    });

    await act(async () => {
      const input = container.querySelector("#confirmation_email") as HTMLInputElement;
      const valueSetter = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )?.set;
      valueSetter?.call(input, "lem@example.com");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });

    await act(async () => {
      const destructiveButton = Array.from(container.querySelectorAll("button")).find(
        (element) =>
          element.textContent?.includes("Delete account") && element.className.includes("bg-red-600"),
      );
      destructiveButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(mutateMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await mutationOptions?.onSuccess?.();
    });

    expect(signOutMock).toHaveBeenCalledTimes(1);
    expect(routerPushMock).toHaveBeenCalledWith("/");
  });

  it("shows an error toast when account deletion fails", async () => {
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
      root.render(<DeleteAccountDialog />);
    });

    await act(async () => {
      await mutationOptions?.onError?.(new Error("Delete failed"));
    });

    expect(toastErrorMock).toHaveBeenCalledWith("Delete failed");
  });
});
