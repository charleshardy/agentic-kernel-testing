// Caching utilities for performance optimization

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  maxSize?: number; // Maximum cache size
}

const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes
const DEFAULT_MAX_SIZE = 100;

/**
 * In-memory cache with TTL and size limits
 */
export class MemoryCache<T = any> {
  private cache: Map<string, CacheEntry<T>> = new Map();
  private ttl: number;
  private maxSize: number;

  constructor(options: CacheOptions = {}) {
    this.ttl = options.ttl || DEFAULT_TTL;
    this.maxSize = options.maxSize || DEFAULT_MAX_SIZE;
  }

  /**
   * Get value from cache
   */
  get(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  /**
   * Set value in cache
   */
  set(key: string, data: T, ttl?: number): void {
    const expiresAt = Date.now() + (ttl || this.ttl);
    
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      expiresAt
    });

    // Enforce max size
    if (this.cache.size > this.maxSize) {
      this.evictOldest();
    }
  }

  /**
   * Check if key exists and is not expired
   */
  has(key: string): boolean {
    return this.get(key) !== null;
  }

  /**
   * Delete key from cache
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Get cache size
   */
  size(): number {
    return this.cache.size;
  }

  /**
   * Evict oldest entry
   */
  private evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      if (entry.timestamp < oldestTime) {
        oldestTime = entry.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  /**
   * Clean up expired entries
   */
  cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
      }
    }
  }
}

/**
 * API response cache
 */
export class APICache {
  private cache: MemoryCache<any>;

  constructor(options: CacheOptions = {}) {
    this.cache = new MemoryCache(options);
  }

  /**
   * Get cached API response
   */
  get(url: string, params?: Record<string, any>): any | null {
    const key = this.generateKey(url, params);
    return this.cache.get(key);
  }

  /**
   * Cache API response
   */
  set(url: string, params: Record<string, any> | undefined, data: any, ttl?: number): void {
    const key = this.generateKey(url, params);
    this.cache.set(key, data, ttl);
  }

  /**
   * Invalidate cache for URL
   */
  invalidate(url: string, params?: Record<string, any>): void {
    const key = this.generateKey(url, params);
    this.cache.delete(key);
  }

  /**
   * Invalidate all cache entries matching URL pattern
   */
  invalidatePattern(pattern: string): void {
    // Simple pattern matching - could be enhanced with regex
    for (const key of Array.from((this.cache as any).cache.keys())) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Generate cache key from URL and params
   */
  private generateKey(url: string, params?: Record<string, any>): string {
    if (!params) {
      return url;
    }
    const sortedParams = Object.keys(params)
      .sort()
      .map(key => `${key}=${JSON.stringify(params[key])}`)
      .join('&');
    return `${url}?${sortedParams}`;
  }
}

/**
 * React hook for cached API calls
 */
export function useCachedAPI<T>(
  url: string,
  params?: Record<string, any>,
  options: CacheOptions = {}
) {
  const cache = React.useMemo(() => new APICache(options), []);
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const fetchData = React.useCallback(async (force = false) => {
    // Check cache first
    if (!force) {
      const cached = cache.get(url, params);
      if (cached) {
        setData(cached);
        return cached;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const queryString = params
        ? '?' + new URLSearchParams(params as any).toString()
        : '';
      const response = await fetch(`${url}${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      cache.set(url, params, result);
      setData(result);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [url, params, cache]);

  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: () => fetchData(true),
    invalidate: () => cache.invalidate(url, params)
  };
}

/**
 * LocalStorage cache with size limits
 */
export class LocalStorageCache {
  private prefix: string;
  private maxSize: number;

  constructor(prefix = 'cache:', maxSize = 5 * 1024 * 1024) { // 5MB default
    this.prefix = prefix;
    this.maxSize = maxSize;
  }

  /**
   * Get value from localStorage
   */
  get<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(this.prefix + key);
      if (!item) return null;

      const entry: CacheEntry<T> = JSON.parse(item);
      
      // Check if expired
      if (Date.now() > entry.expiresAt) {
        this.delete(key);
        return null;
      }

      return entry.data;
    } catch (error) {
      console.error('LocalStorage get error:', error);
      return null;
    }
  }

  /**
   * Set value in localStorage
   */
  set<T>(key: string, data: T, ttl = DEFAULT_TTL): boolean {
    try {
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        expiresAt: Date.now() + ttl
      };

      const serialized = JSON.stringify(entry);
      
      // Check size
      if (serialized.length > this.maxSize) {
        console.warn('Cache entry too large, skipping');
        return false;
      }

      localStorage.setItem(this.prefix + key, serialized);
      return true;
    } catch (error) {
      // Handle quota exceeded
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        this.cleanup();
        try {
          localStorage.setItem(this.prefix + key, JSON.stringify({ data, timestamp: Date.now(), expiresAt: Date.now() + ttl }));
          return true;
        } catch {
          return false;
        }
      }
      console.error('LocalStorage set error:', error);
      return false;
    }
  }

  /**
   * Delete key from localStorage
   */
  delete(key: string): void {
    localStorage.removeItem(this.prefix + key);
  }

  /**
   * Clear all cache entries with prefix
   */
  clear(): void {
    const keys = Object.keys(localStorage);
    for (const key of keys) {
      if (key.startsWith(this.prefix)) {
        localStorage.removeItem(key);
      }
    }
  }

  /**
   * Clean up expired entries
   */
  cleanup(): void {
    const keys = Object.keys(localStorage);
    const now = Date.now();

    for (const key of keys) {
      if (key.startsWith(this.prefix)) {
        try {
          const item = localStorage.getItem(key);
          if (item) {
            const entry = JSON.parse(item);
            if (now > entry.expiresAt) {
              localStorage.removeItem(key);
            }
          }
        } catch {
          // Invalid entry, remove it
          localStorage.removeItem(key);
        }
      }
    }
  }

  /**
   * Get total cache size
   */
  getSize(): number {
    const keys = Object.keys(localStorage);
    let size = 0;

    for (const key of keys) {
      if (key.startsWith(this.prefix)) {
        const item = localStorage.getItem(key);
        if (item) {
          size += item.length;
        }
      }
    }

    return size;
  }
}

// Export singleton instances
export const apiCache = new APICache({ ttl: 5 * 60 * 1000, maxSize: 100 });
export const localCache = new LocalStorageCache();

// React import
import React from 'react';
