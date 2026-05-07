"use client";

import { createContext, useContext, useEffect, useRef, useState } from "react";

type ToastTone = "success" | "error";

type ToastAction = {
  label: string;
  onClick: () => void;
};

type ToastItem = {
  id: number;
  message: string;
  tone: ToastTone;
  persistent: boolean;
  durationMs?: number;
  action?: ToastAction;
  className?: string;
};

type UndoToastOptions = {
  message: string;
  action: ToastAction;
};

type ToastContextValue = {
  success: (message: string) => void;
  error: (message: string) => void;
  showUndoToast: (options: UndoToastOptions) => number;
  dismissToast: (id: number) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

function getToastStyles(tone: ToastTone) {
  if (tone === "error") {
    return "border-l-4 border-[color:color-mix(in_srgb,var(--error)_35%,var(--border))] bg-[color:color-mix(in_srgb,var(--error)_10%,var(--surface))] text-text-primary";
  }

  return "border-l-4 border-[color:color-mix(in_srgb,var(--success)_35%,var(--border))] bg-[color:color-mix(in_srgb,var(--success)_10%,var(--surface))] text-text-primary";
}

function getUndoToastClassName() {
  return "border-l-4 border-zinc-400 bg-zinc-900 text-zinc-100";
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextToastId = useRef(0);
  const timers = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    const activeTimers = timers.current;

    return () => {
      for (const timer of activeTimers.values()) {
        clearTimeout(timer);
      }
    };
  }, []);

  function dismiss(id: number) {
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }

    setToasts((currentToasts) => currentToasts.filter((toast) => toast.id !== id));
  }

  function push(message: string, tone: ToastTone, persistent: boolean) {
    const id = nextToastId.current;
    nextToastId.current += 1;

    setToasts((currentToasts) => [...currentToasts, { id, message, tone, persistent }]);

    if (persistent) {
      return;
    }

    const timer = setTimeout(() => {
      dismiss(id);
    }, 3000);

    timers.current.set(id, timer);
  }

  function showUndoToast(options: UndoToastOptions): number {
    const id = nextToastId.current;
    nextToastId.current += 1;

    setToasts((currentToasts) => [
      ...currentToasts,
      {
        id,
        message: options.message,
        tone: "success",
        persistent: false,
        durationMs: 5000,
        action: options.action,
        className: getUndoToastClassName(),
      },
    ]);

    const timer = setTimeout(() => {
      dismiss(id);
    }, 5000);

    timers.current.set(id, timer);

    return id;
  }

  return (
    <ToastContext.Provider
      value={{
        success: (message) => push(message, "success", false),
        error: (message) => push(message, "error", true),
        showUndoToast,
        dismissToast: dismiss,
      }}
    >
      {children}

      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role={toast.tone === "error" ? "alert" : "status"}
            className={`pointer-events-auto w-full max-w-sm rounded-xl border px-4 py-3 text-sm shadow-lg backdrop-blur ${toast.className ?? getToastStyles(toast.tone)}`}
          >
            <div className="flex items-start justify-between gap-3">
              <p>{toast.message}</p>
              <div className="flex items-center gap-2">
                {toast.action && (
                  <button
                    type="button"
                    onClick={() => {
                      toast.action!.onClick();
                      dismiss(toast.id);
                    }}
                    className="text-zinc-100 underline transition hover:text-zinc-300"
                  >
                    {toast.action.label}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => dismiss(toast.id)}
                  className="text-current/60 transition hover:text-current"
                  aria-label="Dismiss notification"
                >
                  x
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);

  if (context === null) {
    throw new Error("useToast must be used within ToastProvider");
  }

  return context;
}
