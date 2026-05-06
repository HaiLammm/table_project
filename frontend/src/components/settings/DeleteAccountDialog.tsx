"use client";

import { useState } from "react";
import { useClerk, useUser } from "@clerk/nextjs";
import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, LoaderCircle } from "lucide-react";
import { useRouter } from "next/navigation";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { ApiClientError, useApiClient } from "@/lib/api-client";

function getErrorMessage(error: unknown) {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to delete your account";
}

export function DeleteAccountDialog() {
  const apiClient = useApiClient();
  const clerk = useClerk();
  const router = useRouter();
  const { user } = useUser();
  const { error: showError } = useToast();
  const [open, setOpen] = useState(false);
  const [confirmationEmail, setConfirmationEmail] = useState("");

  const userEmail = user?.primaryEmailAddress?.emailAddress ?? user?.emailAddresses[0]?.emailAddress ?? "";
  const deleteDisabled = confirmationEmail !== userEmail || userEmail.length === 0;

  const deleteAccountMutation = useMutation({
    mutationFn: () =>
      apiClient<void>("/users/me", {
        method: "DELETE",
        body: JSON.stringify({ confirmation_email: confirmationEmail }),
      }),
    onSuccess: async () => {
      setOpen(false);
      setConfirmationEmail("");
      await clerk.signOut();
      router.push("/");
    },
    onError: (mutationError) => {
      showError(getErrorMessage(mutationError));
    },
  });

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-[color:color-mix(in_srgb,var(--error)_20%,var(--border))] bg-[color:color-mix(in_srgb,var(--error)_6%,var(--surface))] p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-1">
        <h3 className="text-sm font-medium text-text-primary">Delete account permanently</h3>
        <p className="text-sm text-text-secondary">
          Remove your account, preferences, exports, and any associated learning records. This action is irreversible.
        </p>
      </div>

      <AlertDialog
        open={open}
        onOpenChange={(nextOpen) => {
          setOpen(nextOpen);
          if (!nextOpen) {
            setConfirmationEmail("");
          }
        }}
      >
        <AlertDialogTrigger asChild>
          <Button type="button" variant="ghost" className="text-destructive hover:text-destructive">
            Delete account
          </Button>
        </AlertDialogTrigger>

        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete account?</AlertDialogTitle>
            <AlertDialogDescription>
              Type <span className="font-medium text-text-primary">{userEmail || "your email"}</span> to confirm permanent deletion.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="rounded-xl border border-[color:color-mix(in_srgb,var(--error)_25%,var(--border))] bg-[color:color-mix(in_srgb,var(--error)_8%,var(--surface))] p-4 text-sm text-text-primary">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 size-4 text-destructive" />
              <div className="space-y-1">
                <p className="font-medium">This cannot be undone.</p>
                <p className="text-text-secondary">
                  We will permanently remove your account, exports, and local learning data after confirmation.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="confirmation_email" className="text-sm font-medium text-text-primary">
              Confirmation email
            </label>
            <input
              id="confirmation_email"
              name="confirmation_email"
              type="email"
              value={confirmationEmail}
              disabled={deleteAccountMutation.isPending}
              onChange={(event) => setConfirmationEmail(event.target.value)}
              className="flex w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary shadow-sm outline-none transition focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              placeholder={userEmail || "email@example.com"}
            />
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel asChild>
              <Button type="button" variant="outline" disabled={deleteAccountMutation.isPending}>
                Cancel
              </Button>
            </AlertDialogCancel>

            <AlertDialogAction asChild>
              <Button
                type="button"
                className="bg-red-600 text-white hover:bg-red-700"
                disabled={deleteDisabled || deleteAccountMutation.isPending}
                onClick={(event) => {
                  event.preventDefault();
                  if (!deleteDisabled) {
                    deleteAccountMutation.mutate();
                  }
                }}
              >
                {deleteAccountMutation.isPending ? <LoaderCircle className="size-4 animate-spin" /> : null}
                {deleteAccountMutation.isPending ? "Deleting..." : "Delete account"}
              </Button>
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
