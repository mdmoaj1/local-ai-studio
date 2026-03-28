"use client";

import { AdaptersView } from "@/components/adapters/adapters-view";
import { useAdaptersQuery, useDeleteAdapterMutation, useLoadAdapterMutation } from "@/hooks/use-adapters";

export function AdaptersContainer() {
  const query = useAdaptersQuery();
  const deleteMutation = useDeleteAdapterMutation();
  const loadMutation = useLoadAdapterMutation();

  return <AdaptersView query={query} deleteMutation={deleteMutation} loadMutation={loadMutation} />;
}
