"use client";

import { DatasetsView } from "@/components/datasets/datasets-view";
import { useDatasetsQuery, useDeleteDatasetMutation, useUploadDatasetMutation } from "@/hooks/use-datasets";

export function DatasetsContainer() {
  const query = useDatasetsQuery();
  const uploadMutation = useUploadDatasetMutation();
  const deleteMutation = useDeleteDatasetMutation();

  return (
    <DatasetsView query={query} uploadMutation={uploadMutation} deleteMutation={deleteMutation} />
  );
}
