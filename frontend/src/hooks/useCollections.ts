"use client";

import { useCallback, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useApiClient } from "@/lib/api-client";
import { collectionKeys } from "@/lib/query-keys";
import type {
  AddTermRequest,
  AddTermsRequest,
  AddTermsResponse,
  Collection,
  CollectionCSVImportResponse,
  CollectionCreateRequest,
  CollectionListResponse,
  CollectionResponse,
  CollectionTermListResponse,
  CollectionTermMasteryStatus,
  CollectionUpdateRequest,
} from "@/types/collection";

function buildOptimisticCollection(tempId: number, payload: CollectionCreateRequest): Collection {
  const now = new Date().toISOString();

  return {
    id: tempId,
    name: payload.name,
    icon: payload.icon,
    term_count: 0,
    mastery_percent: 0,
    created_at: now,
    updated_at: now,
  };
}

function replaceCollection(items: Collection[], nextCollection: Collection) {
  return items.map((item) => (item.id === nextCollection.id ? nextCollection : item));
}

function withUpdatedTermCount(collection: Collection, delta: number): Collection {
  return {
    ...collection,
    term_count: Math.max(0, collection.term_count + delta),
  };
}

function useDebounce(value: string, delay: number): string {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function useCollections() {
  const apiClient = useApiClient();

  return useQuery({
    queryKey: collectionKeys.list(),
    queryFn: () => apiClient<CollectionListResponse>("/collections"),
    staleTime: 5 * 60_000,
  });
}

export function useCollectionTerms(
  collectionId: number | null,
  page: number,
  search?: string,
  masteryStatus?: CollectionTermMasteryStatus | null,
) {
  const apiClient = useApiClient();
  const debouncedSearch = useDebounce(search ?? "", 200);
  const effectiveSearch = debouncedSearch.length >= 2 ? debouncedSearch : undefined;
  const effectiveMasteryStatus = masteryStatus ?? undefined;

  return useQuery({
    queryKey:
      collectionId === null
        ? [...collectionKeys.all, "terms", "disabled"]
        : [...collectionKeys.terms(collectionId), { page, search: effectiveSearch, mastery_status: effectiveMasteryStatus }],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (effectiveSearch) {
        params.set("search", effectiveSearch);
      }
      if (effectiveMasteryStatus) {
        params.set("mastery_status", effectiveMasteryStatus);
      }
      return apiClient<CollectionTermListResponse>(
        `/collections/${collectionId}/terms?${params.toString()}`,
      );
    },
    enabled: collectionId !== null,
  });
}

export function useCreateCollection() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CollectionCreateRequest) =>
      apiClient<CollectionResponse>("/collections", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onMutate: async (data) => {
      await queryClient.cancelQueries({ queryKey: collectionKeys.list() });

      const previousList = queryClient.getQueryData<CollectionListResponse>(collectionKeys.list());
      const tempId = -Date.now();
      const optimisticCollection = buildOptimisticCollection(tempId, data);

      queryClient.setQueryData<CollectionListResponse>(collectionKeys.list(), {
        items: [optimisticCollection, ...(previousList?.items ?? [])],
      });

      return { previousList, tempId };
    },
    onError: (_error, _data, context) => {
      if (context?.previousList) {
        queryClient.setQueryData(collectionKeys.list(), context.previousList);
      }
    },
    onSuccess: (collection, _data, context) => {
      const currentList = queryClient.getQueryData<CollectionListResponse>(collectionKeys.list());
      const nextItems = currentList?.items.some((item) => item.id === context?.tempId)
        ? currentList.items.map((item) => (item.id === context?.tempId ? collection : item))
        : [collection, ...(currentList?.items ?? [])];

      queryClient.setQueryData<CollectionListResponse>(collectionKeys.list(), {
        items: nextItems,
      });
      queryClient.setQueryData(collectionKeys.detail(collection.id), collection);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.all });
    },
  });
}

export function useUpdateCollection() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      collectionId,
      data,
    }: {
      collectionId: number;
      data: CollectionUpdateRequest;
    }) =>
      apiClient<CollectionResponse>(`/collections/${collectionId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onMutate: async ({ collectionId, data }) => {
      await queryClient.cancelQueries({ queryKey: collectionKeys.list() });

      const previousList = queryClient.getQueryData<CollectionListResponse>(collectionKeys.list());
      const previousDetail = queryClient.getQueryData<CollectionResponse>(
        collectionKeys.detail(collectionId),
      );

      if (previousList) {
        queryClient.setQueryData<CollectionListResponse>(collectionKeys.list(), {
          items: previousList.items.map((item) =>
            item.id === collectionId ? { ...item, ...data } : item,
          ),
        });
      }

      if (previousDetail) {
        queryClient.setQueryData<CollectionResponse>(collectionKeys.detail(collectionId), {
          ...previousDetail,
          ...data,
        });
      }

      return { previousList, previousDetail, collectionId };
    },
    onError: (_error, _data, context) => {
      if (context?.previousList) {
        queryClient.setQueryData(collectionKeys.list(), context.previousList);
      }
      if (context?.previousDetail) {
        queryClient.setQueryData(collectionKeys.detail(context.collectionId), context.previousDetail);
      }
    },
    onSuccess: (collection) => {
      const currentList = queryClient.getQueryData<CollectionListResponse>(collectionKeys.list());
      if (currentList) {
        queryClient.setQueryData<CollectionListResponse>(collectionKeys.list(), {
          items: replaceCollection(currentList.items, collection),
        });
      }
      queryClient.setQueryData(collectionKeys.detail(collection.id), collection);
    },
    onSettled: (_data, _error, variables) => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.list() });
      queryClient.invalidateQueries({ queryKey: collectionKeys.detail(variables.collectionId) });
    },
  });
}

export function useDeleteCollection() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (collectionId: number) =>
      apiClient<void>(`/collections/${collectionId}`, {
        method: "DELETE",
      }),
    onMutate: async (collectionId) => {
      await queryClient.cancelQueries({ queryKey: collectionKeys.list() });

      const previousList = queryClient.getQueryData<CollectionListResponse>(collectionKeys.list());
      const previousDetail = queryClient.getQueryData<CollectionResponse>(
        collectionKeys.detail(collectionId),
      );

      if (previousList) {
        queryClient.setQueryData<CollectionListResponse>(collectionKeys.list(), {
          items: previousList.items.filter((item) => item.id !== collectionId),
        });
      }

      queryClient.removeQueries({ queryKey: collectionKeys.detail(collectionId) });

      return { previousList, previousDetail, collectionId };
    },
    onError: (_error, _collectionId, context) => {
      if (context?.previousList) {
        queryClient.setQueryData(collectionKeys.list(), context.previousList);
      }
      if (context?.previousDetail) {
        queryClient.setQueryData(collectionKeys.detail(context.collectionId), context.previousDetail);
      }
    },
    onSettled: (_data, _error, collectionId) => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.list() });
      queryClient.removeQueries({ queryKey: collectionKeys.detail(collectionId) });
    },
  });
}

export function useAddTermToCollection(collectionId: number) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AddTermRequest) =>
      apiClient<AddTermsResponse>(`/collections/${collectionId}/terms`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.list() });
      queryClient.invalidateQueries({ queryKey: collectionKeys.detail(collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.terms(collectionId) });
    },
  });
}

export function useAddTermsBulk(collectionId: number) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AddTermsRequest) =>
      apiClient<AddTermsResponse>(`/collections/${collectionId}/terms`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.list() });
      queryClient.invalidateQueries({ queryKey: collectionKeys.detail(collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.terms(collectionId) });
    },
  });
}

export function useRemoveTermFromCollection(collectionId: number) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (termId: number) =>
      apiClient<void>(`/collections/${collectionId}/terms/${termId}`, {
        method: "DELETE",
      }),
    onMutate: async (termId) => {
      await queryClient.cancelQueries({ queryKey: collectionKeys.list() });
      await queryClient.cancelQueries({ queryKey: collectionKeys.detail(collectionId) });
      await queryClient.cancelQueries({ queryKey: collectionKeys.terms(collectionId) });

      const previousList = queryClient.getQueryData<CollectionListResponse>(collectionKeys.list());
      const previousDetail = queryClient.getQueryData<CollectionResponse>(
        collectionKeys.detail(collectionId),
      );
      const previousTerms = queryClient.getQueriesData<CollectionTermListResponse>({
        queryKey: collectionKeys.terms(collectionId),
      });

      if (previousList) {
        queryClient.setQueryData<CollectionListResponse>(collectionKeys.list(), {
          items: previousList.items.map((item) =>
            item.id === collectionId ? withUpdatedTermCount(item, -1) : item,
          ),
        });
      }

      if (previousDetail) {
        queryClient.setQueryData<CollectionResponse>(collectionKeys.detail(collectionId),
          withUpdatedTermCount(previousDetail, -1),
        );
      }

      for (const [queryKey, pageData] of previousTerms) {
        if (!pageData || !pageData.items.some((item) => item.term_id === termId)) {
          continue;
        }

        queryClient.setQueryData<CollectionTermListResponse>(queryKey, {
          ...pageData,
          items: pageData.items.filter((item) => item.term_id !== termId),
          total: Math.max(0, pageData.total - 1),
        });
      }

      return { previousList, previousDetail, previousTerms };
    },
    onError: (_error, _termId, context) => {
      if (context?.previousList) {
        queryClient.setQueryData(collectionKeys.list(), context.previousList);
      }

      if (context?.previousDetail) {
        queryClient.setQueryData(collectionKeys.detail(collectionId), context.previousDetail);
      }

      for (const [queryKey, pageData] of context?.previousTerms ?? []) {
        queryClient.setQueryData(queryKey, pageData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.list() });
      queryClient.invalidateQueries({ queryKey: collectionKeys.detail(collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.terms(collectionId) });
    },
  });
}

export function useImportCSVToCollection(collectionId: number) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      return apiClient<CollectionCSVImportResponse>(`/collections/${collectionId}/import`, {
        method: "POST",
        body: formData,
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.list() });
      queryClient.invalidateQueries({ queryKey: collectionKeys.detail(collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.terms(collectionId) });
    },
  });
}
