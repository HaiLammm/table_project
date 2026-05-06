"use client";

import { Languages } from "lucide-react";
import { Button } from "@/components/ui/button";

interface LanguageToggleProps {
  isParallel: boolean;
  onToggle: () => void;
}

export function LanguageToggle({ isParallel, onToggle }: LanguageToggleProps) {
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onToggle}
      className="flex items-center gap-2"
      title="Toggle parallel view (Tab)"
    >
      <Languages className="size-4" />
      <span>{isParallel ? "Parallel" : "Single"}</span>
    </Button>
  );
}
