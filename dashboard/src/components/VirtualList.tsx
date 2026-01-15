import React, { useState, useEffect, useRef, useCallback } from 'react';

interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
  className?: string;
}

/**
 * Virtual scrolling list component for performance optimization
 * Only renders visible items plus overscan buffer
 */
function VirtualList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 3,
  className = ''
}: VirtualListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate visible range
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleItems = items.slice(startIndex, endIndex + 1);
  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        height: containerHeight,
        overflow: 'auto',
        position: 'relative'
      }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0
          }}
        >
          {visibleItems.map((item, index) => (
            <div
              key={startIndex + index}
              style={{ height: itemHeight }}
            >
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default VirtualList;

/**
 * Hook for virtual scrolling with dynamic item heights
 */
export function useVirtualScroll<T>(
  items: T[],
  containerHeight: number,
  estimatedItemHeight: number,
  overscan = 3
) {
  const [scrollTop, setScrollTop] = useState(0);
  const [itemHeights, setItemHeights] = useState<Map<number, number>>(new Map());
  const itemRefs = useRef<Map<number, HTMLElement>>(new Map());

  // Measure item heights
  const measureItem = useCallback((index: number, element: HTMLElement | null) => {
    if (element) {
      itemRefs.current.set(index, element);
      const height = element.getBoundingClientRect().height;
      setItemHeights(prev => {
        const next = new Map(prev);
        next.set(index, height);
        return next;
      });
    }
  }, []);

  // Calculate positions
  const getItemOffset = useCallback((index: number): number => {
    let offset = 0;
    for (let i = 0; i < index; i++) {
      offset += itemHeights.get(i) || estimatedItemHeight;
    }
    return offset;
  }, [itemHeights, estimatedItemHeight]);

  const getTotalHeight = useCallback((): number => {
    let height = 0;
    for (let i = 0; i < items.length; i++) {
      height += itemHeights.get(i) || estimatedItemHeight;
    }
    return height;
  }, [items.length, itemHeights, estimatedItemHeight]);

  // Find visible range
  const getVisibleRange = useCallback((): [number, number] => {
    let startIndex = 0;
    let currentOffset = 0;

    // Find start index
    for (let i = 0; i < items.length; i++) {
      const itemHeight = itemHeights.get(i) || estimatedItemHeight;
      if (currentOffset + itemHeight > scrollTop) {
        startIndex = Math.max(0, i - overscan);
        break;
      }
      currentOffset += itemHeight;
    }

    // Find end index
    let endIndex = startIndex;
    currentOffset = getItemOffset(startIndex);
    for (let i = startIndex; i < items.length; i++) {
      const itemHeight = itemHeights.get(i) || estimatedItemHeight;
      if (currentOffset > scrollTop + containerHeight) {
        endIndex = Math.min(items.length - 1, i + overscan);
        break;
      }
      currentOffset += itemHeight;
      endIndex = i;
    }

    return [startIndex, endIndex];
  }, [scrollTop, containerHeight, items.length, itemHeights, estimatedItemHeight, overscan, getItemOffset]);

  return {
    scrollTop,
    setScrollTop,
    measureItem,
    getItemOffset,
    getTotalHeight,
    getVisibleRange
  };
}

/**
 * Virtual table component for large datasets
 */
interface VirtualTableProps<T> {
  data: T[];
  columns: Array<{
    key: string;
    title: string;
    width?: number;
    render?: (value: any, record: T, index: number) => React.ReactNode;
  }>;
  rowHeight: number;
  containerHeight: number;
  onRowClick?: (record: T, index: number) => void;
}

export function VirtualTable<T extends Record<string, any>>({
  data,
  columns,
  rowHeight,
  containerHeight,
  onRowClick
}: VirtualTableProps<T>) {
  return (
    <div style={{ border: '1px solid #f0f0f0' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid #f0f0f0',
          background: '#fafafa',
          fontWeight: 600,
          height: rowHeight
        }}
      >
        {columns.map(col => (
          <div
            key={col.key}
            style={{
              flex: col.width ? `0 0 ${col.width}px` : 1,
              padding: '8px 16px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}
          >
            {col.title}
          </div>
        ))}
      </div>

      {/* Body with virtual scrolling */}
      <VirtualList
        items={data}
        itemHeight={rowHeight}
        containerHeight={containerHeight - rowHeight}
        renderItem={(record, index) => (
          <div
            style={{
              display: 'flex',
              borderBottom: '1px solid #f0f0f0',
              cursor: onRowClick ? 'pointer' : 'default',
              height: rowHeight
            }}
            onClick={() => onRowClick?.(record, index)}
          >
            {columns.map(col => (
              <div
                key={col.key}
                style={{
                  flex: col.width ? `0 0 ${col.width}px` : 1,
                  padding: '8px 16px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
              >
                {col.render
                  ? col.render(record[col.key], record, index)
                  : record[col.key]}
              </div>
            ))}
          </div>
        )}
      />
    </div>
  );
}
