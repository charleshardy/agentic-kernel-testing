import { useState, useEffect, useMemo, useCallback } from 'react'

export interface VirtualizationConfig {
  itemHeight: number
  containerHeight: number
  overscan?: number
  threshold?: number
}

export interface VirtualizedItem<T> {
  index: number
  data: T
  style: React.CSSProperties
}

export const useVirtualization = <T>(
  items: T[],
  config: VirtualizationConfig
) => {
  const [scrollTop, setScrollTop] = useState(0)
  const [isScrolling, setIsScrolling] = useState(false)
  
  const {
    itemHeight,
    containerHeight,
    overscan = 5,
    threshold = items.length > 100 ? 100 : items.length
  } = config

  // Only virtualize if we have more items than threshold
  const shouldVirtualize = items.length > threshold

  // Calculate visible range
  const visibleRange = useMemo(() => {
    if (!shouldVirtualize) {
      return { start: 0, end: items.length }
    }

    const start = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan)
    const visibleCount = Math.ceil(containerHeight / itemHeight)
    const end = Math.min(items.length, start + visibleCount + overscan * 2)

    return { start, end }
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length, shouldVirtualize])

  // Get virtualized items
  const virtualizedItems = useMemo((): VirtualizedItem<T>[] => {
    if (!shouldVirtualize) {
      return items.map((data, index) => ({
        index,
        data,
        style: {}
      }))
    }

    const result: VirtualizedItem<T>[] = []
    
    for (let i = visibleRange.start; i < visibleRange.end; i++) {
      result.push({
        index: i,
        data: items[i],
        style: {
          position: 'absolute',
          top: i * itemHeight,
          left: 0,
          right: 0,
          height: itemHeight
        }
      })
    }

    return result
  }, [items, visibleRange, itemHeight, shouldVirtualize])

  // Handle scroll with throttling
  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = event.currentTarget.scrollTop
    setScrollTop(newScrollTop)
    
    if (!isScrolling) {
      setIsScrolling(true)
    }

    // Debounce scroll end detection
    const timeoutId = setTimeout(() => {
      setIsScrolling(false)
    }, 150)

    return () => clearTimeout(timeoutId)
  }, [isScrolling])

  // Container props for the scrollable container
  const containerProps = useMemo(() => ({
    style: {
      height: containerHeight,
      overflow: 'auto' as const,
      position: 'relative' as const
    },
    onScroll: handleScroll
  }), [containerHeight, handleScroll])

  // Inner container props (for absolute positioning)
  const innerProps = useMemo(() => ({
    style: shouldVirtualize ? {
      height: items.length * itemHeight,
      position: 'relative' as const
    } : {}
  }), [items.length, itemHeight, shouldVirtualize])

  return {
    virtualizedItems,
    containerProps,
    innerProps,
    isScrolling,
    shouldVirtualize,
    visibleRange,
    totalHeight: items.length * itemHeight
  }
}