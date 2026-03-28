"use client";

import type { ReactNode } from "react";

import { TooltipProvider } from "@/components/ui/tooltip";

import { QueryProvider } from "./query-provider";

type AppProvidersProps = {
  children: ReactNode;
};

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryProvider>
      <TooltipProvider delayDuration={200}>{children}</TooltipProvider>
    </QueryProvider>
  );
}
