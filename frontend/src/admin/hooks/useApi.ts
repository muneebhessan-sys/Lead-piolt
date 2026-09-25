import { useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { QueryKey } from '@tanstack/react-query';

const API_BASE = '/api/v1';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

async function fetchApi<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...init } = options;
  const url = new URL(API_BASE + path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
    });
  }
  const response = await fetch(url.toString(), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {}),
    },
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail || data?.message || `Request failed: ${response.status}`;
    throw new Error(message);
  }
  return data as T;
}

export function useApi() {
  const queryClient = useQueryClient();

  const get = useCallback(<T,>(path: string, params?: RequestOptions['params'], queryOptions?: { enabled?: boolean; staleTime?: number }) => {
    return useQuery<T, Error>({
      queryKey: [path, params] as QueryKey,
      queryFn: () => fetchApi<T>(path, { params }),
      enabled: queryOptions?.enabled ?? true,
      staleTime: queryOptions?.staleTime ?? 30_000,
      refetchOnWindowFocus: false,
    });
  }, []);

  const post = useCallback(<T,>(path: string, body: unknown, mutationOptions?: { onSuccess?: (data: T) => void; invalidateKeys?: QueryKey[] }) => {
    return useMutation<T, Error, unknown>({
      mutationFn: () => fetchApi<T>(path, { method: 'POST', body: JSON.stringify(body) }),
      onSuccess: (data) => {
        mutationOptions?.onSuccess?.(data);
        mutationOptions?.invalidateKeys?.forEach(key => queryClient.invalidateQueries({ queryKey: key }));
      },
    });
  }, [queryClient]);

  const put = useCallback(<T,>(path: string, body: unknown, mutationOptions?: { onSuccess?: (data: T) => void; invalidateKeys?: QueryKey[] }) => {
    return useMutation<T, Error, unknown>({
      mutationFn: () => fetchApi<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
      onSuccess: (data) => {
        mutationOptions?.onSuccess?.(data);
        mutationOptions?.invalidateKeys?.forEach(key => queryClient.invalidateQueries({ queryKey: key }));
      },
    });
  }, [queryClient]);

  const patch = useCallback(<T,>(path: string, body: unknown, mutationOptions?: { onSuccess?: (data: T) => void; invalidateKeys?: QueryKey[] }) => {
    return useMutation<T, Error, unknown>({
      mutationFn: () => fetchApi<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
      onSuccess: (data) => {
        mutationOptions?.onSuccess?.(data);
        mutationOptions?.invalidateKeys?.forEach(key => queryClient.invalidateQueries({ queryKey: key }));
      },
    });
  }, [queryClient]);

  const del = useCallback(<T,>(path: string, mutationOptions?: { onSuccess?: (data: T) => void; invalidateKeys?: QueryKey[] }) => {
    return useMutation<T, Error, void>({
      mutationFn: () => fetchApi<T>(path, { method: 'DELETE' }),
      onSuccess: (data) => {
        mutationOptions?.onSuccess?.(data);
        mutationOptions?.invalidateKeys?.forEach(key => queryClient.invalidateQueries({ queryKey: key }));
      },
    });
  }, [queryClient]);

  return useMemo(() => ({ get, post, put, patch, delete: del }), [get, post, put, patch, del]);
}

export function useApiCall<T>(path: string, options: RequestOptions = {}) {
  return fetchApi<T>(path, options);
}