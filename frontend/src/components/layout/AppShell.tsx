"use client";

import { useState } from "react";

import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex min-h-screen">
        <Sidebar mobileOpen={mobileOpen} onMobileOpenChange={setMobileOpen} />

        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar
            mobileOpen={mobileOpen}
            onMenuToggle={() => setMobileOpen((open) => !open)}
          />

          <main id="main-content" className="flex-1 overflow-x-hidden">
            <div className="mx-auto flex w-full max-w-[720px] flex-col px-4 py-6 sm:px-6 lg:px-8">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
