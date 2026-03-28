"use client";

import type { ReactNode } from "react";

import { useSystemWebSocket } from "@/hooks/use-system-websocket";

type SystemMetricsBridgeProps = {
  children: ReactNode;
};

export function SystemMetricsBridge({ children }: SystemMetricsBridgeProps) {
  useSystemWebSocket(true);
  return children;
}
