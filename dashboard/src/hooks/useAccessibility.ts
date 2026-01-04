import { useEffect, useCallback, useRef, useState } from 'react'

// Keyboard navigation hook
export const useKeyboardNavigation = (
  items: any[],
  onSelect?: (index: number, item: any) => void,
  options: {
    loop?: boolean
    disabled?: boolean
    initialIndex?: number
  } = {}
) => {
  const { loop = true, disabled = false, initialIndex = -1 } = options
  const [focusedIndex, setFocusedIndex] = useState(initialIndex)
  const containerRef = useRef<HTMLElement>(null)

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (disabled || items.length === 0) return

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        setFocusedIndex(prev => {
          const next = prev + 1
          if (next >= items.length) {
            return loop ? 0 : prev
          }
          return next
        })
        break

      case 'ArrowUp':
        event.preventDefault()
        setFocusedIndex(prev => {
          const next = prev - 1
          if (next < 0) {
            return loop ? items.length - 1 : prev
          }
          return next
        })
        break

      case 'Home':
        event.preventDefault()
        setFocusedIndex(0)
        break

      case 'End':
        event.preventDefault()
        setFocusedIndex(items.length - 1)
        break

      case 'Enter':
      case ' ':
        event.preventDefault()
        if (focusedIndex >= 0 && focusedIndex < items.length && onSelect) {
          onSelect(focusedIndex, items[focusedIndex])
        }
        break

      case 'Escape':
        event.preventDefault()
        setFocusedIndex(-1)
        break
    }
  }, [disabled, items, loop, focusedIndex, onSelect])

  useEffect(() => {
    const container = containerRef.current
    if (container) {
      container.addEventListener('keydown', handleKeyDown)
      return () => container.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown])

  const getItemProps = useCallback((index: number) => ({
    tabIndex: focusedIndex === index ? 0 : -1,
    'aria-selected': focusedIndex === index,
    role: 'option',
    onFocus: () => setFocusedIndex(index),
    onMouseEnter: () => setFocusedIndex(index)
  }), [focusedIndex])

  const getContainerProps = useCallback(() => ({
    ref: containerRef,
    role: 'listbox',
    'aria-activedescendant': focusedIndex >= 0 ? `item-${focusedIndex}` : undefined,
    tabIndex: 0
  }), [focusedIndex])

  return {
    focusedIndex,
    setFocusedIndex,
    getItemProps,
    getContainerProps
  }
}

// Screen reader announcements
export const useScreenReader = () => {
  const announcementRef = useRef<HTMLDivElement>(null)

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!announcementRef.current) {
      // Create announcement element if it doesn't exist
      const element = document.createElement('div')
      element.setAttribute('aria-live', priority)
      element.setAttribute('aria-atomic', 'true')
      element.style.position = 'absolute'
      element.style.left = '-10000px'
      element.style.width = '1px'
      element.style.height = '1px'
      element.style.overflow = 'hidden'
      document.body.appendChild(element)
      announcementRef.current = element
    }

    // Update the message
    announcementRef.current.setAttribute('aria-live', priority)
    announcementRef.current.textContent = message

    // Clear after announcement
    setTimeout(() => {
      if (announcementRef.current) {
        announcementRef.current.textContent = ''
      }
    }, 1000)
  }, [])

  useEffect(() => {
    return () => {
      if (announcementRef.current && announcementRef.current.parentNode) {
        announcementRef.current.parentNode.removeChild(announcementRef.current)
      }
    }
  }, [])

  return { announce }
}

// Focus management
export const useFocusManagement = () => {
  const previousFocusRef = useRef<HTMLElement | null>(null)

  const saveFocus = useCallback(() => {
    previousFocusRef.current = document.activeElement as HTMLElement
  }, [])

  const restoreFocus = useCallback(() => {
    if (previousFocusRef.current && previousFocusRef.current.focus) {
      previousFocusRef.current.focus()
    }
  }, [])

  const trapFocus = useCallback((container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    const firstElement = focusableElements[0] as HTMLElement
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault()
            lastElement.focus()
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault()
            firstElement.focus()
          }
        }
      }
    }

    container.addEventListener('keydown', handleKeyDown)
    
    // Focus first element
    if (firstElement) {
      firstElement.focus()
    }

    return () => {
      container.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  return { saveFocus, restoreFocus, trapFocus }
}

// ARIA attributes helper
export const useAriaAttributes = () => {
  const generateId = useCallback((prefix: string = 'aria') => {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`
  }, [])

  const getComboboxProps = useCallback((
    isExpanded: boolean,
    listboxId: string,
    activeDescendant?: string
  ) => ({
    role: 'combobox',
    'aria-expanded': isExpanded,
    'aria-haspopup': 'listbox',
    'aria-controls': listboxId,
    'aria-activedescendant': activeDescendant
  }), [])

  const getListboxProps = useCallback((id: string, labelledBy?: string) => ({
    id,
    role: 'listbox',
    'aria-labelledby': labelledBy
  }), [])

  const getOptionProps = useCallback((
    id: string,
    isSelected: boolean,
    isDisabled: boolean = false
  ) => ({
    id,
    role: 'option',
    'aria-selected': isSelected,
    'aria-disabled': isDisabled
  }), [])

  const getProgressProps = useCallback((
    value: number,
    max: number = 100,
    label?: string
  ) => ({
    role: 'progressbar',
    'aria-valuenow': value,
    'aria-valuemin': 0,
    'aria-valuemax': max,
    'aria-label': label || `Progress: ${value} of ${max}`
  }), [])

  const getAlertProps = useCallback((live: 'polite' | 'assertive' = 'polite') => ({
    role: 'alert',
    'aria-live': live,
    'aria-atomic': true
  }), [])

  return {
    generateId,
    getComboboxProps,
    getListboxProps,
    getOptionProps,
    getProgressProps,
    getAlertProps
  }
}

// Color contrast checker
export const useColorContrast = () => {
  const checkContrast = useCallback((foreground: string, background: string) => {
    // Convert hex to RGB
    const hexToRgb = (hex: string) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : null
    }

    // Calculate relative luminance
    const getLuminance = (r: number, g: number, b: number) => {
      const [rs, gs, bs] = [r, g, b].map(c => {
        c = c / 255
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
      })
      return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
    }

    const fgRgb = hexToRgb(foreground)
    const bgRgb = hexToRgb(background)

    if (!fgRgb || !bgRgb) return null

    const fgLuminance = getLuminance(fgRgb.r, fgRgb.g, fgRgb.b)
    const bgLuminance = getLuminance(bgRgb.r, bgRgb.g, bgRgb.b)

    const contrast = (Math.max(fgLuminance, bgLuminance) + 0.05) / 
                    (Math.min(fgLuminance, bgLuminance) + 0.05)

    return {
      ratio: contrast,
      AA: contrast >= 4.5,
      AAA: contrast >= 7,
      AALarge: contrast >= 3,
      AAALarge: contrast >= 4.5
    }
  }, [])

  return { checkContrast }
}

// Reduced motion detection
export const useReducedMotion = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches)
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return prefersReducedMotion
}