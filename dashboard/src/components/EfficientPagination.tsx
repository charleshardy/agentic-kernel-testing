import React, { useState, useCallback, useMemo } from 'react';
import { Pagination, Select } from 'antd';

const { Option } = Select;

interface PaginationConfig {
  current: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean;
  pageSizeOptions?: number[];
}

interface EfficientPaginationProps {
  total: number;
  defaultPageSize?: number;
  defaultCurrent?: number;
  pageSizeOptions?: number[];
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean;
  onChange?: (page: number, pageSize: number) => void;
  onShowSizeChange?: (current: number, size: number) => void;
}

/**
 * Efficient pagination component with performance optimizations
 */
export const EfficientPagination: React.FC<EfficientPaginationProps> = ({
  total,
  defaultPageSize = 20,
  defaultCurrent = 1,
  pageSizeOptions = [10, 20, 50, 100],
  showSizeChanger = true,
  showQuickJumper = true,
  showTotal = true,
  onChange,
  onShowSizeChange
}) => {
  const [current, setCurrent] = useState(defaultCurrent);
  const [pageSize, setPageSize] = useState(defaultPageSize);

  const handleChange = useCallback((page: number, newPageSize: number) => {
    setCurrent(page);
    if (newPageSize !== pageSize) {
      setPageSize(newPageSize);
      onShowSizeChange?.(page, newPageSize);
    }
    onChange?.(page, newPageSize);
  }, [pageSize, onChange, onShowSizeChange]);

  const showTotalText = useMemo(() => {
    if (!showTotal) return undefined;
    return (total: number, range: [number, number]) =>
      `${range[0]}-${range[1]} of ${total} items`;
  }, [showTotal]);

  return (
    <Pagination
      current={current}
      pageSize={pageSize}
      total={total}
      onChange={handleChange}
      showSizeChanger={showSizeChanger}
      showQuickJumper={showQuickJumper}
      showTotal={showTotalText}
      pageSizeOptions={pageSizeOptions}
    />
  );
};

/**
 * Hook for managing pagination state
 */
export function usePagination(
  initialPageSize = 20,
  initialCurrent = 1
) {
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [current, setCurrent] = useState(initialCurrent);

  const handlePageChange = useCallback((page: number, newPageSize: number) => {
    setCurrent(page);
    if (newPageSize !== pageSize) {
      setPageSize(newPageSize);
      // Reset to first page when page size changes
      setCurrent(1);
    }
  }, [pageSize]);

  const reset = useCallback(() => {
    setCurrent(1);
    setPageSize(initialPageSize);
  }, [initialPageSize]);

  return {
    pageSize,
    current,
    setPageSize,
    setCurrent,
    handlePageChange,
    reset
  };
}

/**
 * Hook for paginated data with caching
 */
export function usePaginatedData<T>(
  fetchFunc: (page: number, pageSize: number) => Promise<{ data: T[]; total: number }>,
  initialPageSize = 20
) {
  const [data, setData] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { pageSize, current, handlePageChange, reset } = usePagination(initialPageSize);

  // Cache for loaded pages
  const cache = useMemo(() => new Map<string, { data: T[]; total: number }>(), []);

  const loadPage = useCallback(async (page: number, size: number) => {
    const cacheKey = `${page}-${size}`;
    
    // Check cache first
    const cached = cache.get(cacheKey);
    if (cached) {
      setData(cached.data);
      setTotal(cached.total);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await fetchFunc(page, size);
      cache.set(cacheKey, result);
      setData(result.data);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [fetchFunc, cache]);

  // Load data when page or pageSize changes
  React.useEffect(() => {
    loadPage(current, pageSize);
  }, [current, pageSize, loadPage]);

  const invalidateCache = useCallback(() => {
    cache.clear();
    loadPage(current, pageSize);
  }, [cache, current, pageSize, loadPage]);

  return {
    data,
    total,
    loading,
    error,
    pageSize,
    current,
    handlePageChange,
    reset,
    invalidateCache
  };
}

/**
 * Infinite scroll pagination component
 */
interface InfiniteScrollProps<T> {
  loadMore: (page: number) => Promise<T[]>;
  renderItem: (item: T, index: number) => React.ReactNode;
  hasMore: boolean;
  threshold?: number;
  loader?: React.ReactNode;
}

export function InfiniteScroll<T>({
  loadMore,
  renderItem,
  hasMore,
  threshold = 100,
  loader
}: InfiniteScrollProps<T>) {
  const [items, setItems] = useState<T[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const observerRef = useRef<HTMLDivElement>(null);

  const loadNextPage = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    try {
      const newItems = await loadMore(page);
      setItems(prev => [...prev, ...newItems]);
      setPage(prev => prev + 1);
    } catch (error) {
      console.error('Failed to load more items:', error);
    } finally {
      setLoading(false);
    }
  }, [loading, hasMore, page, loadMore]);

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasMore && !loading) {
          loadNextPage();
        }
      },
      { rootMargin: `${threshold}px` }
    );

    const currentRef = observerRef.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [hasMore, loading, threshold, loadNextPage]);

  return (
    <div>
      {items.map((item, index) => (
        <div key={index}>{renderItem(item, index)}</div>
      ))}
      {hasMore && (
        <div ref={observerRef} style={{ padding: '20px', textAlign: 'center' }}>
          {loading && (loader || 'Loading...')}
        </div>
      )}
    </div>
  );
}

/**
 * Cursor-based pagination for large datasets
 */
export function useCursorPagination<T extends { id: string }>(
  fetchFunc: (cursor: string | null, limit: number) => Promise<{ data: T[]; nextCursor: string | null }>,
  limit = 20
) {
  const [data, setData] = useState<T[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadMore = useCallback(async () => {
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      const result = await fetchFunc(cursor, limit);
      setData(prev => [...prev, ...result.data]);
      setNextCursor(result.nextCursor);
      setCursor(result.nextCursor);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [cursor, limit, loading, fetchFunc]);

  const reset = useCallback(() => {
    setData([]);
    setCursor(null);
    setNextCursor(null);
  }, []);

  const hasMore = nextCursor !== null;

  return {
    data,
    loading,
    error,
    hasMore,
    loadMore,
    reset
  };
}

export default EfficientPagination;
