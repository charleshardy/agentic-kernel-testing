import React, { Suspense, lazy } from 'react';
import { Spin } from 'antd';

interface LazyLoadProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  minHeight?: number;
}

/**
 * Lazy load wrapper with loading fallback
 */
export const LazyLoad: React.FC<LazyLoadProps> = ({
  children,
  fallback,
  minHeight = 200
}) => {
  const defaultFallback = (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: minHeight,
        width: '100%'
      }}
    >
      <Spin size="large" tip="Loading..." />
    </div>
  );

  return (
    <Suspense fallback={fallback || defaultFallback}>
      {children}
    </Suspense>
  );
};

/**
 * Intersection Observer based lazy loading
 */
interface IntersectionLazyLoadProps {
  children: React.ReactNode;
  placeholder?: React.ReactNode;
  rootMargin?: string;
  threshold?: number;
  onVisible?: () => void;
}

export const IntersectionLazyLoad: React.FC<IntersectionLazyLoadProps> = ({
  children,
  placeholder,
  rootMargin = '50px',
  threshold = 0.01,
  onVisible
}) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
          onVisible?.();
        }
      },
      { rootMargin, threshold }
    );

    const currentRef = ref.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [isVisible, rootMargin, threshold, onVisible]);

  return (
    <div ref={ref}>
      {isVisible ? children : placeholder || <div style={{ minHeight: 100 }} />}
    </div>
  );
};

/**
 * Image lazy loading component
 */
interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  placeholder?: string;
  onLoad?: () => void;
  onError?: () => void;
}

export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  placeholder,
  onLoad,
  onError,
  ...props
}) => {
  const [imageSrc, setImageSrc] = React.useState<string | undefined>(placeholder);
  const [isLoading, setIsLoading] = React.useState(true);
  const imgRef = React.useRef<HTMLImageElement>(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setImageSrc(src);
          if (imgRef.current) {
            observer.unobserve(imgRef.current);
          }
        }
      },
      { rootMargin: '50px' }
    );

    const currentRef = imgRef.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [src]);

  const handleLoad = () => {
    setIsLoading(false);
    onLoad?.();
  };

  const handleError = () => {
    setIsLoading(false);
    onError?.();
  };

  return (
    <img
      ref={imgRef}
      src={imageSrc}
      alt={alt}
      onLoad={handleLoad}
      onError={handleError}
      style={{
        opacity: isLoading ? 0.5 : 1,
        transition: 'opacity 0.3s',
        ...props.style
      }}
      {...props}
    />
  );
};

/**
 * Code splitting helper for route-based lazy loading
 */
export function lazyLoadRoute(
  importFunc: () => Promise<{ default: React.ComponentType<any> }>,
  fallback?: React.ReactNode
) {
  const LazyComponent = lazy(importFunc);

  return (props: any) => (
    <LazyLoad fallback={fallback}>
      <LazyComponent {...props} />
    </LazyLoad>
  );
}

/**
 * Preload component for better UX
 */
export function preloadComponent(
  importFunc: () => Promise<{ default: React.ComponentType<any> }>
): void {
  // Trigger the import to start loading
  importFunc();
}

/**
 * Hook for lazy loading data
 */
export function useLazyLoad<T>(
  loadFunc: () => Promise<T>,
  deps: React.DependencyList = []
) {
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);
  const [shouldLoad, setShouldLoad] = React.useState(false);

  React.useEffect(() => {
    if (!shouldLoad) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    loadFunc()
      .then(result => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch(err => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Unknown error'));
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [shouldLoad, ...deps]);

  return {
    data,
    loading,
    error,
    load: () => setShouldLoad(true),
    reset: () => {
      setData(null);
      setError(null);
      setShouldLoad(false);
    }
  };
}

/**
 * Batch loader for multiple resources
 */
export class BatchLoader<K, V> {
  private queue: Map<K, Array<(value: V) => void>> = new Map();
  private batchTimeout: NodeJS.Timeout | null = null;
  private batchDelay: number;
  private loadFunc: (keys: K[]) => Promise<Map<K, V>>;

  constructor(
    loadFunc: (keys: K[]) => Promise<Map<K, V>>,
    batchDelay = 10
  ) {
    this.loadFunc = loadFunc;
    this.batchDelay = batchDelay;
  }

  load(key: K): Promise<V> {
    return new Promise((resolve) => {
      // Add to queue
      if (!this.queue.has(key)) {
        this.queue.set(key, []);
      }
      this.queue.get(key)!.push(resolve);

      // Schedule batch
      if (!this.batchTimeout) {
        this.batchTimeout = setTimeout(() => {
          this.executeBatch();
        }, this.batchDelay);
      }
    });
  }

  private async executeBatch(): Promise<void> {
    const keys = Array.from(this.queue.keys());
    const callbacks = new Map(this.queue);
    
    this.queue.clear();
    this.batchTimeout = null;

    try {
      const results = await this.loadFunc(keys);
      
      for (const [key, value] of results.entries()) {
        const keyCallbacks = callbacks.get(key);
        if (keyCallbacks) {
          keyCallbacks.forEach(callback => callback(value));
        }
      }
    } catch (error) {
      console.error('Batch load error:', error);
    }
  }
}

export default LazyLoad;
