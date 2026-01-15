/**
 * React hooks for API calls with loading, error, and caching support
 */

import { useState, useEffect, useCallback } from 'react';
import { APIError } from '../api/client';

interface UseAPIOptions {
  immediate?: boolean;
  cache?: boolean;
  cacheDuration?: number;
}

interface UseAPIResult<T> {
  data: T | null;
  loading: boolean;
  error: APIError | null;
  execute: (...args: any[]) => Promise<T | null>;
  reset: () => void;
}

/**
 * Hook for making API calls with automatic loading and error handling
 */
export function useAPI<T>(
  apiFunction: (...args: any[]) => Promise<T>,
  options: UseAPIOptions = {}
): UseAPIResult<T> {
  const { immediate = false, cache = false, cacheDuration = 5 * 60 * 1000 } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<APIError | null>(null);

  const execute = useCallback(
    async (...args: any[]): Promise<T | null> => {
      try {
        setLoading(true);
        setError(null);

        // Check cache if enabled
        if (cache) {
          const cacheKey = `api_cache_${apiFunction.name}_${JSON.stringify(args)}`;
          const cached = sessionStorage.getItem(cacheKey);
          if (cached) {
            const { data: cachedData, timestamp } = JSON.parse(cached);
            if (Date.now() - timestamp < cacheDuration) {
              setData(cachedData);
              setLoading(false);
              return cachedData;
            }
          }
        }

        const result = await apiFunction(...args);
        setData(result);

        // Store in cache if enabled
        if (cache) {
          const cacheKey = `api_cache_${apiFunction.name}_${JSON.stringify(args)}`;
          sessionStorage.setItem(
            cacheKey,
            JSON.stringify({ data: result, timestamp: Date.now() })
          );
        }

        return result;
      } catch (err) {
        const apiError = err instanceof APIError ? err : new APIError(String(err), 500);
        setError(apiError);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, cache, cacheDuration]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  return { data, loading, error, execute, reset };
}

/**
 * Hook for polling API endpoints at regular intervals
 */
export function useAPIPolling<T>(
  apiFunction: (...args: any[]) => Promise<T>,
  interval: number = 5000,
  args: any[] = []
): UseAPIResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);

  const execute = useCallback(async (...executeArgs: any[]): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiFunction(...executeArgs);
      setData(result);
      return result;
    } catch (err) {
      const apiError = err instanceof APIError ? err : new APIError(String(err), 500);
      setError(apiError);
      return null;
    } finally {
      setLoading(false);
    }
  }, [apiFunction]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  useEffect(() => {
    // Initial fetch
    execute(...args);

    // Set up polling
    const intervalId = setInterval(() => {
      execute(...args);
    }, interval);

    return () => clearInterval(intervalId);
  }, [execute, interval, ...args]);

  return { data, loading, error, execute, reset };
}

/**
 * Hook for mutations (POST, PUT, DELETE) with optimistic updates
 */
export function useMutation<T, TVariables = any>(
  mutationFunction: (variables: TVariables) => Promise<T>,
  options?: {
    onSuccess?: (data: T) => void;
    onError?: (error: APIError) => void;
  }
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | null>(null);

  const mutate = useCallback(
    async (variables: TVariables): Promise<T | null> => {
      try {
        setLoading(true);
        setError(null);
        const result = await mutationFunction(variables);
        setData(result);
        options?.onSuccess?.(result);
        return result;
      } catch (err) {
        const apiError = err instanceof APIError ? err : new APIError(String(err), 500);
        setError(apiError);
        options?.onError?.(apiError);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [mutationFunction, options]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, mutate, reset };
}

/**
 * Hook for paginated API calls
 */
export function usePaginatedAPI<T>(
  apiFunction: (params: { limit: number; offset: number; [key: string]: any }) => Promise<{ data: T[]; total: number }>,
  pageSize: number = 20
) {
  const [data, setData] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | null>(null);

  const fetchPage = useCallback(
    async (pageNumber: number, additionalParams: Record<string, any> = {}) => {
      try {
        setLoading(true);
        setError(null);
        const offset = (pageNumber - 1) * pageSize;
        const result = await apiFunction({ limit: pageSize, offset, ...additionalParams });
        setData(result.data);
        setTotal(result.total);
        setPage(pageNumber);
      } catch (err) {
        const apiError = err instanceof APIError ? err : new APIError(String(err), 500);
        setError(apiError);
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, pageSize]
  );

  const nextPage = useCallback(() => {
    if (page * pageSize < total) {
      fetchPage(page + 1);
    }
  }, [page, pageSize, total, fetchPage]);

  const prevPage = useCallback(() => {
    if (page > 1) {
      fetchPage(page - 1);
    }
  }, [page, fetchPage]);

  const goToPage = useCallback(
    (pageNumber: number) => {
      fetchPage(pageNumber);
    },
    [fetchPage]
  );

  useEffect(() => {
    fetchPage(1);
  }, [fetchPage]);

  return {
    data,
    total,
    page,
    pageSize,
    loading,
    error,
    nextPage,
    prevPage,
    goToPage,
    hasNextPage: page * pageSize < total,
    hasPrevPage: page > 1,
    totalPages: Math.ceil(total / pageSize),
  };
}
